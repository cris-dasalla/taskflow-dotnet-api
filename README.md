# TaskFlow API

A clean, production-style **task & project management REST API** built with ASP.NET Core (.NET 10), Entity Framework Core, and JWT authentication.

It demonstrates the things a backend role actually cares about: a layered architecture, secure auth, validation, pagination & filtering, consistent error handling, and interactive API documentation.

![.NET](https://img.shields.io/badge/.NET-10-512BD4)
![C#](https://img.shields.io/badge/C%23-13-239120)
![EF Core](https://img.shields.io/badge/EF%20Core-10-512BD4)
![License](https://img.shields.io/badge/license-MIT-blue)

---

## ✨ Features

- 🔐 **JWT authentication** — register & login, passwords hashed with ASP.NET Core's `PasswordHasher`
- ✅ **Full task CRUD** — create, read, update, delete
- 👥 **Assign tasks to users** — dedicated assign/unassign endpoint
- 🔎 **Filtering & search** — by status, priority, assignee, and free-text search
- 📄 **Pagination** — page/pageSize with rich metadata (total count, total pages, has next/previous)
- 🧱 **Consistent error handling** — RFC 7807 `ProblemDetails` responses via global middleware
- 📚 **Swagger / OpenAPI UI** — explore and test every endpoint in the browser, with bearer-token support
- 🌱 **Auto migrate + seed** — runs migrations and seeds demo data on first start, so it works out of the box

---

## 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Language | C# 13 / .NET 10 |
| Web | ASP.NET Core Web API (controllers) |
| Data | Entity Framework Core 10 |
| Database | SQLite (zero-setup; swap to SQL Server in one line — see below) |
| Auth | JWT Bearer tokens |
| Docs | Swagger / Swashbuckle |

---

## 🚀 Getting Started

### Prerequisites
- [.NET 10 SDK](https://dotnet.microsoft.com/download)

### Run it

```bash
git clone https://github.com/cris-dasalla/taskflow-dotnet-api.git
cd taskflow-dotnet-api/src/TaskFlow.Api
dotnet run
```

That's it — no database setup required. On first run the app creates a SQLite file, applies migrations, and seeds demo data.

Then open the Swagger UI at the URL printed in the console (e.g. **http://localhost:5080**).

### Demo login

A demo account is seeded automatically:

| Email | Password |
|---|---|
| `demo@taskflow.dev` | `Demo123!` |

1. `POST /api/auth/login` with those credentials.
2. Copy the `token` from the response.
3. In Swagger, click **Authorize** and paste the token.
4. Call the protected `/api/tasks` endpoints.

---

## 📡 API Endpoints

| Method | Route | Auth | Description |
|---|---|:--:|---|
| `POST` | `/api/auth/register` | — | Create an account, returns a JWT |
| `POST` | `/api/auth/login` | — | Log in, returns a JWT |
| `GET` | `/api/tasks` | ✅ | List tasks (filtering, search, pagination) |
| `GET` | `/api/tasks/{id}` | ✅ | Get a single task |
| `POST` | `/api/tasks` | ✅ | Create a task |
| `PUT` | `/api/tasks/{id}` | ✅ | Update a task |
| `PATCH` | `/api/tasks/{id}/assignee` | ✅ | Assign / unassign a task |
| `DELETE` | `/api/tasks/{id}` | ✅ | Delete a task |

### List query parameters

`GET /api/tasks?page=1&pageSize=20&status=Todo&priority=High&assignedToId=2&search=design`

| Param | Type | Notes |
|---|---|---|
| `page` | int | Defaults to 1 |
| `pageSize` | int | Defaults to 20, capped at 100 |
| `status` | enum | `Todo`, `InProgress`, `Done` |
| `priority` | enum | `Low`, `Medium`, `High` |
| `assignedToId` | int | Filter by assignee |
| `search` | string | Case-insensitive match on title/description |

---

## 🏗 Project Structure

```
src/TaskFlow.Api/
├── Controllers/      # HTTP endpoints (thin — delegate to services)
├── Services/         # Business logic + interfaces (Auth, Tasks, Token, CurrentUser)
├── Models/           # EF Core entities (User, TaskItem) + enums
├── DTOs/             # Request/response contracts (Auth, Tasks, Common)
├── Data/             # DbContext, migrations, seeder
├── Middleware/       # Global exception → ProblemDetails handler
├── Common/           # Domain exceptions, JWT settings
└── Program.cs        # Composition root: DI, auth, Swagger, pipeline
```

The design keeps **controllers thin** and pushes logic into **services** behind interfaces, so the code is easy to read, test, and extend.

---

## 🗄 Using SQL Server instead of SQLite

The app uses SQLite by default for a zero-setup experience. To use SQL Server:

1. Add the provider: `dotnet add package Microsoft.EntityFrameworkCore.SqlServer`
2. In `Program.cs`, change `UseSqlite(...)` to `UseSqlServer(...)`.
3. Update the `ConnectionStrings:Default` value in `appsettings.json`.

The rest of the code is provider-agnostic.

---

## 📸 Screenshots

> _Add a screenshot of the Swagger UI here once you run it (`docs/swagger.png`)._

---

## 📝 License

MIT — see [LICENSE](LICENSE).

---

Built by **Cris Dasalla** · [GitHub](https://github.com/cris-dasalla)
