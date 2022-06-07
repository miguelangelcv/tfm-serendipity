using System;

namespace SerendipityWebApp.Data
{
    public class LoginState
    {
        private string _accessToken;
        public bool IsLoggedIn { get; set; }
        public string UserName { get; set; }
        public string UserId { get; set; }

        public event Action OnChange;


        public void SetLogin(bool login, string userId, string user, string accessToken)
        {
            IsLoggedIn = login;
            UserName = user;
            UserId = userId;
            _accessToken = accessToken;

            NotifyStateChanged();
        }

        private void NotifyStateChanged() => OnChange?.Invoke();
        public string GetAccessToken() => _accessToken;
    }
}
