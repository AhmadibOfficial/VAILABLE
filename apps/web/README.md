# Web application

The existing FastAPI application renders `shell.html` and the catalog from the
canonical Python tool registry. It serves `app.js` and `style.css` at `/assets`.
There is no frontend build step or TypeScript source.

From the repository root, install the Python dependencies with
`python -m pip install -r services/api/requirements-dev.txt` and install system
Chromium (`chromium` must be on PATH). Then, from `apps/web`:

- `npm ci --ignore-scripts`: validate/install the dependency-free npm package.
- `npm run dev`: run the application with reload at http://127.0.0.1:8000.
- `npm start`: run the application without reload.
- `npm run lint`: check browser JavaScript syntax with Node's parser. This is
  syntax checking only, not a full style or semantic linter.
- `npm test`: run frontend browser tests and the existing responsive/real PDF
  merge browser tests against an automatically started local API server.
- `npm run test:api`: run the API and PDF processing regression suite.
- `npm run test:contracts`: check rendered catalog, Coming Soon pages, assets
  and accessible merge controls in process, without a local server socket.

No typecheck script is provided because the application is plain JavaScript
without a configured static type system. Browser tests exercise DOM behavior,
API contracts, validation, download state and server errors. Python dependencies
remain in the existing requirements files; npm has no runtime dependencies.
