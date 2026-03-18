# TBOS Frontend

Production-ready frontend architecture for TechBuilt Open School (TBOS).

## Stack

- Next.js (App Router)
- TypeScript
- TailwindCSS + ShadCN UI
- Axios
- React Query
- Zustand

## Run

1. Install dependencies:
	npm install
2. Configure environment:
	.env.local
3. Start development:
	npm run dev
4. Build for production:
	npm run build

## Environment Variables

Create .env.local with:

NEXT_PUBLIC_API_URL=http://localhost:8000/api

## Architecture

- app: routes, global layout, loading/error UI
- components: layout, providers, auth, reusable UI wrappers
- lib: axios client, query client, constants, cookie helpers
- services: API service modules
- store: Zustand stores
- types: shared TypeScript types

## Notes

- Role-based route control is implemented via middleware.
- JWT is persisted in secure same-site cookies on the client.
- Global request/query errors surface through toast notifications.
