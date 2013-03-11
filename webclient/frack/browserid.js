define(
  ["dojo/_base/lang", "dojo/_base/Deferred"],
  function (lang, Deferred) {
    return function (validateAssertion, loginHandler, logoutHandler, reportError) {
      return {
        onLogout: function () {
          var loginTarget = logoutHandler();
          loginTarget.onclick(function(e) {
                                navigator.id.request();
                                return false;
                              });
        },
        onLogin: function (response) {
          var self = this;
          if (response.ok) {
            var logoutTarget = loginHandler(response.key, response.username);
            logoutTarget.onclick(function (e) {
                                   navigator.id.logout();
                                 });
          } else {
            this.onLogout();
          }
        },
        onAssertion: function (assertion) {
            var self = this;
          if (assertion !== null) {
            var r = validateAssertion(assertion);
            r.then(lang.hitch(this, "onLogin"),
                   reportError);
            return r;
          } else {
            return null;
          }
        },
        start: function (key, username, getLoginButton) {
          if (username) {
            this.onLogin({ok: true, key: key, username: username});
          } else {
            getLoginButton().onclick(function(e) {
                                       navigator.id.request();
                                     });
          }
          // args get called in window context, so gotta bind them
          navigator.id.watch({loggedInUser: username,
                              onlogin: lang.hitch(this, "onAssertion"),
                              onlogout: lang.hitch(this, "onLogout")
                              });
        }
      };
    };
  });