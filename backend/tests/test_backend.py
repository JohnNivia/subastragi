"""SQLite-backed integration tests for core domain services."""

import asyncio
import unittest
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import app.main  # noqa: F401
from app.adjudications.services import close_auction
from app.auctions.models import Auction
from app.auctions.schemas import AuctionUpdate
from app.auctions.services import update_auction
from app.auth import services as auth_services
from app.bids import services as bid_services
from app.bids.models import Bid
from app.bids.schemas import BidCreate
from app.cattle_lots.models import Breed, CattleLot
from app.cattle_lots.services import get_lot
from app.core.config import Settings
from app.core.database import Base
from app.core.exceptions import register_exception_handlers
from app.core.security import verify_password
from app.users.models import Role, User
from app.users.schemas import RoleName
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from starlette.requests import Request


class BackendServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine, expire_on_commit=False)
        self.roles = {
            name: Role(nombre_rol=name, descripcion=name.title())
            for name in ("ADMINISTRADOR", "GANADERO", "COMPRADOR")
        }
        self.db.add_all(self.roles.values())
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()

    def make_user(self, role_name: str, email: str | None = None) -> User:
        user = User(
            email=email or f"{uuid4()}@example.test",
            password_hash="unused",
            nombre_completo="Usuario de prueba",
            documento_identidad=str(uuid4()),
            estado=True,
            roles=[self.roles[role_name]],
        )
        self.db.add(user)
        self.db.commit()
        return user

    def make_auction(self, seller: User, *, close_at: datetime) -> Auction:
        breed = Breed(nombre_raza=f"Raza-{uuid4()}", proposito="Carne", estado=True)
        self.db.add(breed)
        self.db.flush()
        lot = CattleLot(
            ganadero_id=seller.id,
            raza_id=breed.id,
            codigo_lote=f"LOT-{uuid4().hex[:12]}",
            cantidad_cabezas=2,
            peso_promedio_kg=300.0,
            vacunacion_al_dia=True,
            ubicacion_hacienda="Finca de prueba",
            estado_lote="EN_SUBASTA",
        )
        self.db.add(lot)
        self.db.flush()
        auction = Auction(
            lote_id=lot.id,
            precio_base_kilo=Decimal("100.00"),
            incremento_minimo_puja=Decimal("5.00"),
            fecha_inicio=datetime.now(UTC) - timedelta(minutes=5),
            fecha_cierre=close_at,
            estado_subasta="ACTIVA",
        )
        self.db.add(auction)
        self.db.commit()
        return auction

    def test_registration_hashes_password_and_rotates_refresh_token(self) -> None:
        user = auth_services.register(
            self.db,
            email="buyer@example.com",
            password="correct-horse-battery-7",
            nombre_completo="Comprador de Prueba",
            documento_identidad="ID-90001",
            telefono=None,
            rol=RoleName.COMPRADOR,
        )
        self.assertNotEqual(user.password_hash, "correct-horse-battery-7")
        self.assertTrue(verify_password("correct-horse-battery-7", user.password_hash))

        _, _, first_refresh = auth_services.authenticate(
            self.db, "buyer@example.com", "correct-horse-battery-7"
        )
        _, _, second_refresh = auth_services.rotate_refresh_token(
            self.db, first_refresh
        )
        with self.assertRaises(HTTPException) as error:
            auth_services.rotate_refresh_token(self.db, first_refresh)
        self.assertEqual(error.exception.status_code, 401)
        auth_services.revoke_refresh_token(self.db, second_refresh)
        with self.assertRaises(HTTPException):
            auth_services.rotate_refresh_token(self.db, second_refresh)

    def test_password_change_revokes_refresh_sessions(self) -> None:
        user = auth_services.register(
            self.db,
            email="password@example.com",
            password="correct-horse-battery-7",
            nombre_completo="Usuario de Prueba",
            documento_identidad="ID-PASSWORD",
            telefono=None,
            rol=RoleName.COMPRADOR,
        )
        _, _, refresh = auth_services.authenticate(
            self.db, "password@example.com", "correct-horse-battery-7"
        )
        auth_services.change_password(
            self.db, user, "correct-horse-battery-7", "new-secure-password-8"
        )
        with self.assertRaises(HTTPException) as error:
            auth_services.rotate_refresh_token(self.db, refresh)
        self.assertEqual(error.exception.status_code, 401)
        with self.assertRaises(HTTPException):
            auth_services.authenticate(
                self.db, "password@example.com", "correct-horse-battery-7"
            )
        auth_services.authenticate(
            self.db, "password@example.com", "new-secure-password-8"
        )

    def test_public_registration_cannot_grant_admin_role(self) -> None:
        with self.assertRaises(HTTPException) as error:
            auth_services.register(
                self.db,
                email="admin@example.com",
                password="correct-horse-battery-7",
                nombre_completo="Admin",
                documento_identidad="ID-ADMIN",
                telefono=None,
                rol=RoleName.ADMINISTRADOR,
            )
        self.assertEqual(error.exception.status_code, 403)

    def test_validation_errors_do_not_echo_submitted_passwords(self) -> None:
        request = Request(
            {"type": "http", "method": "POST", "path": "/api/v1/auth/login"}
        )
        validation_error = RequestValidationError(
            [
                {
                    "loc": ("body", "password"),
                    "msg": "Invalid value",
                    "type": "value_error",
                    "input": "do-not-echo-this-password",
                }
            ]
        )
        test_app = FastAPI()
        register_exception_handlers(test_app)
        handler = test_app.exception_handlers[RequestValidationError]
        response = asyncio.run(handler(request, validation_error))
        self.assertNotIn(b"do-not-echo-this-password", response.body)
        self.assertEqual(response.status_code, 422)

    def test_database_url_does_not_require_separate_db_password(self) -> None:
        configured = Settings(
            _env_file=None,
            database_url="postgresql://postgres:secret@localhost/subastagro_db",
            secret_key="test-signing-key-with-at-least-32-characters",
            environment="test",
        )
        self.assertEqual(
            configured.sqlalchemy_database_url,
            "postgresql://postgres:secret@localhost/subastagro_db",
        )

    def test_bid_must_meet_current_offer_plus_increment(self) -> None:
        seller = self.make_user("GANADERO")
        buyer = self.make_user("COMPRADOR")
        auction = self.make_auction(
            seller, close_at=datetime.now(UTC) + timedelta(minutes=10)
        )
        self.db.add(
            Bid(
                subasta_id=auction.id,
                comprador_id=buyer.id,
                monto_ofertado_kilo=Decimal("100.00"),
                fecha_hora_puja=datetime.now(UTC),
            )
        )
        self.db.commit()

        with self.assertRaises(HTTPException) as error:
            bid_services.place_bid(
                self.db,
                BidCreate(subasta_id=auction.id, monto_ofertado_kilo=Decimal("104.99")),
                buyer,
            )
        self.assertEqual(error.exception.status_code, 400)
        accepted = bid_services.place_bid(
            self.db,
            BidCreate(subasta_id=auction.id, monto_ofertado_kilo=Decimal("105.00")),
            buyer,
        )
        self.assertEqual(accepted.monto_ofertado_kilo, Decimal("105.00"))

    def test_lot_ownership_hides_other_sellers_lots(self) -> None:
        seller = self.make_user("GANADERO")
        other_seller = self.make_user("GANADERO")
        auction = self.make_auction(
            seller, close_at=datetime.now(UTC) + timedelta(minutes=10)
        )
        lot = self.db.get(CattleLot, auction.lote_id)
        with self.assertRaises(HTTPException) as error:
            get_lot(self.db, lot.id, owner_id=other_seller.id)
        self.assertEqual(error.exception.status_code, 404)

    def test_scheduled_auction_can_be_updated_before_start(self) -> None:
        seller = self.make_user("GANADERO")
        auction = self.make_auction(
            seller, close_at=datetime.now(UTC) + timedelta(days=2)
        )
        auction.estado_subasta = "PROGRAMADA"
        auction.fecha_inicio = datetime.now(UTC) + timedelta(hours=1)
        self.db.commit()
        updated = update_auction(
            self.db,
            auction.id,
            AuctionUpdate(incremento_minimo_puja=Decimal("10.00")),
        )
        self.assertEqual(updated.incremento_minimo_puja, Decimal("10.00"))

    def test_closeout_creates_correct_total_and_unique_guide(self) -> None:
        seller = self.make_user("GANADERO")
        buyer = self.make_user("COMPRADOR")
        auction = self.make_auction(
            seller, close_at=datetime.now(UTC) - timedelta(minutes=1)
        )
        self.db.add(
            Bid(
                subasta_id=auction.id,
                comprador_id=buyer.id,
                monto_ofertado_kilo=Decimal("125.50"),
                fecha_hora_puja=datetime.now(UTC) - timedelta(minutes=2),
            )
        )
        self.db.commit()

        adjudication = close_auction(self.db, auction.id)
        self.assertEqual(adjudication.monto_total_final, Decimal("75300.00"))
        self.assertTrue(adjudication.guia_movilizacion_codigo.startswith("SAG-"))
        self.assertEqual(self.db.get(Auction, auction.id).estado_subasta, "FINALIZADA")


if __name__ == "__main__":
    unittest.main()
