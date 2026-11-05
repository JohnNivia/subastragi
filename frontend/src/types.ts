export type RoleName = "ADMINISTRADOR" | "GANADERO" | "COMPRADOR";

export interface Role {
  id: number;
  nombre_rol: RoleName;
  descripcion: string;
}

export interface User {
  id: string;
  email: string;
  nombre_completo: string;
  documento_identidad: string;
  telefono: string | null;
  estado: boolean;
  fecha_creacion: string;
  roles: Role[];
}

export interface TokenResponse {
  access_token: string;
  token_type: "bearer";
  expires_in: number;
  usuario: User;
}

export interface Breed {
  id: string;
  nombre_raza: string;
  proposito: string;
  estado: boolean;
}

export interface CattleLot {
  id: string;
  ganadero_id: string;
  raza_id: string;
  codigo_lote: string;
  cantidad_cabezas: number;
  peso_promedio_kg: number;
  vacunacion_al_dia: boolean;
  ubicacion_hacienda: string;
  estado_lote: string;
}

export interface Auction {
  id: string;
  lote_id: string;
  precio_base_kilo: string;
  incremento_minimo_puja: string;
  fecha_inicio: string;
  fecha_cierre: string;
  estado_subasta: "PROGRAMADA" | "ACTIVA" | "FINALIZADA" | "DESIERTA";
}

export interface Bid {
  id: string;
  subasta_id: string;
  comprador_id: string;
  monto_ofertado_kilo: string;
  fecha_hora_puja: string;
}

export interface Adjudication {
  id: string;
  subasta_id: string;
  comprador_ganador_id: string;
  puja_ganadora_id: string;
  monto_total_final: string;
  guia_movilizacion_codigo: string;
  estado_pago: "PENDIENTE" | "PAGADO" | "RECHAZADO";
  fecha_cierre: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  nombre_completo: string;
  documento_identidad: string;
  telefono: string | null;
  rol: Exclude<RoleName, "ADMINISTRADOR">;
}
