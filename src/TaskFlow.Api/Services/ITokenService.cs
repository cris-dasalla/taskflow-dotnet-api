using TaskFlow.Api.Models;

namespace TaskFlow.Api.Services;

public interface ITokenService
{
    (string Token, DateTime ExpiresAt) CreateToken(User user);
}
