using TaskFlow.Api.DTOs.Common;
using TaskFlow.Api.DTOs.Tasks;

namespace TaskFlow.Api.Services;

public interface ITaskService
{
    Task<PagedResult<TaskResponse>> GetTasksAsync(TaskQueryParameters query);
    Task<TaskResponse> GetByIdAsync(int id);
    Task<TaskResponse> CreateAsync(CreateTaskRequest request);
    Task<TaskResponse> UpdateAsync(int id, UpdateTaskRequest request);
    Task DeleteAsync(int id);
    Task<TaskResponse> AssignAsync(int id, int? assignedToId);
}
