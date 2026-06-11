using Microsoft.AspNetCore.Identity;
using Microsoft.EntityFrameworkCore;
using TaskFlow.Api.Models;

namespace TaskFlow.Api.Data;

/// <summary>Applies migrations and seeds a demo user + sample tasks on startup if the DB is empty.</summary>
public static class DbSeeder
{
    public const string DemoEmail = "demo@taskflow.dev";
    public const string DemoPassword = "Demo123!";

    public static async Task MigrateAndSeedAsync(IServiceProvider services)
    {
        using var scope = services.CreateScope();
        var db = scope.ServiceProvider.GetRequiredService<AppDbContext>();
        var hasher = scope.ServiceProvider.GetRequiredService<IPasswordHasher<User>>();

        await db.Database.MigrateAsync();

        if (await db.Users.AnyAsync())
            return;

        var now = DateTime.UtcNow;

        var demo = new User
        {
            Email = DemoEmail,
            DisplayName = "Demo User",
            CreatedAt = now
        };
        demo.PasswordHash = hasher.HashPassword(demo, DemoPassword);

        var teammate = new User
        {
            Email = "alex@taskflow.dev",
            DisplayName = "Alex Rivera",
            CreatedAt = now
        };
        teammate.PasswordHash = hasher.HashPassword(teammate, DemoPassword);

        db.Users.AddRange(demo, teammate);
        await db.SaveChangesAsync();

        db.Tasks.AddRange(
            new TaskItem
            {
                Title = "Set up project repository",
                Description = "Initialize the repo, add README and CI.",
                Status = TaskState.Done,
                Priority = TaskPriority.High,
                CreatedById = demo.Id,
                AssignedToId = demo.Id,
                CreatedAt = now,
                UpdatedAt = now
            },
            new TaskItem
            {
                Title = "Design task data model",
                Description = "Define User and TaskItem entities and relationships.",
                Status = TaskState.InProgress,
                Priority = TaskPriority.High,
                DueDate = now.AddDays(2),
                CreatedById = demo.Id,
                AssignedToId = teammate.Id,
                CreatedAt = now,
                UpdatedAt = now
            },
            new TaskItem
            {
                Title = "Write API documentation",
                Description = "Document all endpoints in the README and Swagger.",
                Status = TaskState.Todo,
                Priority = TaskPriority.Medium,
                DueDate = now.AddDays(5),
                CreatedById = demo.Id,
                CreatedAt = now,
                UpdatedAt = now
            });

        await db.SaveChangesAsync();
    }
}
