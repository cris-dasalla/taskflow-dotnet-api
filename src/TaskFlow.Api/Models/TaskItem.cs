namespace TaskFlow.Api.Models;

/// <summary>
/// A unit of work that can be tracked, prioritized, and assigned to a user.
/// </summary>
public class TaskItem
{
    public int Id { get; set; }

    public string Title { get; set; } = string.Empty;

    public string? Description { get; set; }

    public TaskState Status { get; set; } = TaskState.Todo;

    public TaskPriority Priority { get; set; } = TaskPriority.Medium;

    public DateTime? DueDate { get; set; }

    public DateTime CreatedAt { get; set; }

    public DateTime UpdatedAt { get; set; }

    /// <summary>User who created the task.</summary>
    public int CreatedById { get; set; }
    public User? CreatedBy { get; set; }

    /// <summary>User the task is assigned to (optional).</summary>
    public int? AssignedToId { get; set; }
    public User? AssignedTo { get; set; }
}
