using System.Security.Claims;
using TaskFlow.Api.Common;

namespace TaskFlow.Api.Services;

/// <summary>Reads the current user's id from the JWT claims on the active HTTP request.</summary>
public class CurrentUser : ICurrentUser
{
    private readonly IHttpContextAccessor _accessor;

    public CurrentUser(IHttpContextAccessor accessor) => _accessor = accessor;

    public int Id
    {
        get
        {
            var value = _accessor.HttpContext?.User.FindFirstValue(ClaimTypes.NameIdentifier);
            if (int.TryParse(value, out var id))
                return id;

            throw new UnauthorizedException("No authenticated user on the current request.");
        }
    }
}
