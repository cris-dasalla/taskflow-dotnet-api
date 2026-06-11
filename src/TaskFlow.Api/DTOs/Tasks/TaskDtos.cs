using System.ComponentModel.DataAnnotations;
using TaskFlow.Api.Models;

namespace TaskFlow.Api.DTOs.Tasks;

public class CreateTaskRequest
{
    [Required, MaxLength(200)]
    public string Title { get; set; } = string.Empty;

    [MaxLength(2000)]
    public string? Description { get; set; }

    public TaskPriority Priority { get; set; } = TaskPriority.Medium;

    public DateTime? DueDate { get; set; }

    /// <summary>Optional user to assign the task to on creation.</summary>
    public int? AssignedToId { get; set; }
}

public class UpdateTaskRequest
{
    [Required, MaxLength(200)]
    public string Title { get; set; } = string.Empty;

    [MaxLength(2000)]
    public string? Description { get; set; }

    public TaskState Status { get; set; }

    public TaskPriority Priority { get; set; }

    public DateTime? DueDate { get; set; }

    public int? AssignedToId { get; set; }
}

/// <summary>Lightweight user reference embedded in task responses.</summary>
public class UserSummary
{
    public int Id { get; set; }
    public string DisplayName { get; set; } = string.Empty;
    public string Email { get; set; } = string.Empty;
}

public class TaskResponse
{
    public int Id { get; set; }
    public string Title { get; set; } = string.Empty;
    public string? Description { get; set; }
    public TaskState Status { get; set; }
    public TaskPriority Priority { get; set; }
    public DateTime? DueDate { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
    public UserSummary? CreatedBy { get; set; }
    public UserSummary? AssignedTo { get; set; }
}

/// <summary>Query parameters for listing tasks: filtering, paging, and sorting.</summary>
public class TaskQueryParameters
{
    private const int MaxPageSize = 100;
    private int _pageSize = 20;

    public int Page { get; set; } = 1;

    public int PageSize
    {
        get => _pageSize;
        set => _pageSize = value is < 1 or > MaxPageSize ? MaxPageSize : value;
    }

    /// <summary>Filter by status (Todo/InProgress/Done).</summary>
    public TaskState? Status { get; set; }

    /// <summary>Filter by priority.</summary>
    public TaskPriority? Priority { get; set; }

    /// <summary>Filter to tasks assigned to a specific user.</summary>
    public int? AssignedToId { get; set; }

    /// <summary>Case-insensitive search across title and description.</summary>
    public string? Search { get; set; }
}
