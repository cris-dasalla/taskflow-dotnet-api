using Microsoft.EntityFrameworkCore;
using TaskFlow.Api.Common;
using TaskFlow.Api.Data;
using TaskFlow.Api.DTOs.Common;
using TaskFlow.Api.DTOs.Tasks;
using TaskFlow.Api.Models;

namespace TaskFlow.Api.Services;

public class TaskService : ITaskService
{
    private readonly AppDbContext _db;
    private readonly ICurrentUser _currentUser;

    public TaskService(AppDbContext db, ICurrentUser currentUser)
    {
        _db = db;
        _currentUser = currentUser;
    }

    public async Task<PagedResult<TaskResponse>> GetTasksAsync(TaskQueryParameters query)
    {
        IQueryable<TaskItem> tasks = _db.Tasks
            .AsNoTracking()
            .Include(t => t.CreatedBy)
            .Include(t => t.AssignedTo);

        if (query.Status is not null)
            tasks = tasks.Where(t => t.Status == query.Status);

        if (query.Priority is not null)
            tasks = tasks.Where(t => t.Priority == query.Priority);

        if (query.AssignedToId is not null)
            tasks = tasks.Where(t => t.AssignedToId == query.AssignedToId);

        if (!string.IsNullOrWhiteSpace(query.Search))
        {
            var term = query.Search.Trim();
            tasks = tasks.Where(t =>
                EF.Functions.Like(t.Title, $"%{term}%") ||
                (t.Description != null && EF.Functions.Like(t.Description, $"%{term}%")));
        }

        var totalCount = await tasks.CountAsync();

        var entities = await tasks
            .OrderByDescending(t => t.Priority)
            .ThenBy(t => t.DueDate ?? DateTime.MaxValue)
            .ThenByDescending(t => t.CreatedAt)
            .Skip((query.Page - 1) * query.PageSize)
            .Take(query.PageSize)
            .ToListAsync();

        var items = entities.Select(ToResponse).ToList();

        return new PagedResult<TaskResponse>
        {
            Items = items,
            Page = query.Page,
            PageSize = query.PageSize,
            TotalCount = totalCount
        };
    }

    public async Task<TaskResponse> GetByIdAsync(int id)
    {
        var task = await _db.Tasks
            .AsNoTracking()
            .Include(t => t.CreatedBy)
            .Include(t => t.AssignedTo)
            .FirstOrDefaultAsync(t => t.Id == id);

        return task is null
            ? throw new NotFoundException($"Task {id} was not found.")
            : ToResponse(task);
    }

    public async Task<TaskResponse> CreateAsync(CreateTaskRequest request)
    {
        await EnsureAssigneeExistsAsync(request.AssignedToId);

        var now = DateTime.UtcNow;
        var task = new TaskItem
        {
            Title = request.Title.Trim(),
            Description = request.Description?.Trim(),
            Priority = request.Priority,
            Status = TaskState.Todo,
            DueDate = request.DueDate,
            AssignedToId = request.AssignedToId,
            CreatedById = _currentUser.Id,
            CreatedAt = now,
            UpdatedAt = now
        };

        _db.Tasks.Add(task);
        await _db.SaveChangesAsync();

        return await GetByIdAsync(task.Id);
    }

    public async Task<TaskResponse> UpdateAsync(int id, UpdateTaskRequest request)
    {
        var task = await _db.Tasks.FirstOrDefaultAsync(t => t.Id == id)
                   ?? throw new NotFoundException($"Task {id} was not found.");

        await EnsureAssigneeExistsAsync(request.AssignedToId);

        task.Title = request.Title.Trim();
        task.Description = request.Description?.Trim();
        task.Status = request.Status;
        task.Priority = request.Priority;
        task.DueDate = request.DueDate;
        task.AssignedToId = request.AssignedToId;
        task.UpdatedAt = DateTime.UtcNow;

        await _db.SaveChangesAsync();
        return await GetByIdAsync(task.Id);
    }

    public async Task DeleteAsync(int id)
    {
        var task = await _db.Tasks.FirstOrDefaultAsync(t => t.Id == id)
                   ?? throw new NotFoundException($"Task {id} was not found.");

        _db.Tasks.Remove(task);
        await _db.SaveChangesAsync();
    }

    public async Task<TaskResponse> AssignAsync(int id, int? assignedToId)
    {
        var task = await _db.Tasks.FirstOrDefaultAsync(t => t.Id == id)
                   ?? throw new NotFoundException($"Task {id} was not found.");

        await EnsureAssigneeExistsAsync(assignedToId);

        task.AssignedToId = assignedToId;
        task.UpdatedAt = DateTime.UtcNow;
        await _db.SaveChangesAsync();

        return await GetByIdAsync(task.Id);
    }

    private async Task EnsureAssigneeExistsAsync(int? assignedToId)
    {
        if (assignedToId is null)
            return;

        if (!await _db.Users.AnyAsync(u => u.Id == assignedToId))
            throw new ValidationFailedException($"Cannot assign task: user {assignedToId} does not exist.");
    }

    private static TaskResponse ToResponse(TaskItem t) => new()
    {
        Id = t.Id,
        Title = t.Title,
        Description = t.Description,
        Status = t.Status,
        Priority = t.Priority,
        DueDate = t.DueDate,
        CreatedAt = t.CreatedAt,
        UpdatedAt = t.UpdatedAt,
        CreatedBy = t.CreatedBy is null ? null : new UserSummary
        {
            Id = t.CreatedBy.Id,
            DisplayName = t.CreatedBy.DisplayName,
            Email = t.CreatedBy.Email
        },
        AssignedTo = t.AssignedTo is null ? null : new UserSummary
        {
            Id = t.AssignedTo.Id,
            DisplayName = t.AssignedTo.DisplayName,
            Email = t.AssignedTo.Email
        }
    };
}
