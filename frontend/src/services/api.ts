import { api } from "../api/axios";
import { endpoints } from "../api/endpoints";
import type {
  Adjudication,
  Auction,
  Bid,
  Breed,
  CattleLot,
  RegisterPayload,
  TokenResponse,
  User,
} from "../types";

export const authService = {
  login: async (email: string, password: string) =>
    (await api.post<TokenResponse>(endpoints.auth.login, { email, password }))
      .data,
  register: async (payload: RegisterPayload) =>
    (await api.post<User>(endpoints.auth.register, payload)).data,
  refresh: async () =>
    (await api.post<TokenResponse>(endpoints.auth.refresh)).data,
  logout: async () => api.post(endpoints.auth.logout),
};

export const userService = {
  me: async () => (await api.get<User>(endpoints.users.me)).data,
  list: async () => (await api.get<User[]>(endpoints.users.list)).data,
  update: async (id: string, payload: Record<string, unknown>) =>
    (await api.patch<User>(endpoints.users.byId(id), payload)).data,
};

export const breedService = {
  list: async () => (await api.get<Breed[]>(endpoints.breeds.list)).data,
  create: async (payload: { nombre_raza: string; proposito: string }) =>
    (await api.post<Breed>(endpoints.breeds.create, payload)).data,
  update: async (id: string, payload: Record<string, unknown>) =>
    (await api.patch<Breed>(endpoints.breeds.byId(id), payload)).data,
};

export const lotService = {
  list: async () => (await api.get<CattleLot[]>(endpoints.lots.list)).data,
  create: async (payload: Record<string, unknown>) =>
    (await api.post<CattleLot>(endpoints.lots.create, payload)).data,
  update: async (id: string, payload: Record<string, unknown>) =>
    (await api.patch<CattleLot>(endpoints.lots.byId(id), payload)).data,
  updateStatus: async (id: string, estado_lote: string) =>
    (await api.patch<CattleLot>(endpoints.lots.status(id), { estado_lote }))
      .data,
};

export const auctionService = {
  list: async () => (await api.get<Auction[]>(endpoints.auctions.list)).data,
  create: async (payload: Record<string, unknown>) =>
    (await api.post<Auction>(endpoints.auctions.create, payload)).data,
  update: async (id: string, payload: Record<string, unknown>) =>
    (await api.patch<Auction>(endpoints.auctions.byId(id), payload)).data,
};

export const bidService = {
  list: async () => (await api.get<Bid[]>(endpoints.bids.list)).data,
  create: async (payload: { subasta_id: string; monto_ofertado_kilo: number }) =>
    (await api.post<Bid>(endpoints.bids.create, payload)).data,
};

export const adjudicationService = {
  list: async () =>
    (await api.get<Adjudication[]>(endpoints.adjudications.list)).data,
  closeAuction: async (auctionId: string) =>
    (
      await api.post<Adjudication | null>(
        endpoints.adjudications.closeAuction(auctionId),
      )
    ).data,
  updatePayment: async (id: string, estado_pago: string) =>
    (
      await api.patch<Adjudication>(endpoints.adjudications.payment(id), {
        estado_pago,
      })
    ).data,
};
