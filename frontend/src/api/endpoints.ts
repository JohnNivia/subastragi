export const endpoints = {
  auth: {
    login: "/auth/login",
    register: "/auth/register",
    refresh: "/auth/refresh",
    logout: "/auth/logout",
  },
  users: {
    me: "/users/me",
    list: "/users",
    byId: (id: string) => `/users/${id}`,
  },
  breeds: {
    list: "/breeds",
    create: "/breeds",
    byId: (id: string) => `/breeds/${id}`,
  },
  lots: {
    list: "/lots",
    create: "/lots",
    byId: (id: string) => `/lots/${id}`,
    status: (id: string) => `/lots/${id}/status`,
  },
  auctions: {
    list: "/auctions",
    create: "/auctions",
    byId: (id: string) => `/auctions/${id}`,
  },
  bids: {
    list: "/bids",
    create: "/bids",
    byId: (id: string) => `/bids/${id}`,
  },
  adjudications: {
    list: "/adjudications",
    closeAuction: (auctionId: string) =>
      `/adjudications/auctions/${auctionId}/close`,
    byId: (id: string) => `/adjudications/${id}`,
    payment: (id: string) => `/adjudications/${id}/payment`,
  },
} as const;
