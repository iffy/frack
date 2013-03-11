define(
  ["dojo/io-query", "dojo/_base/query",
   "frack/service", "frack/browserid",
   "frack/ticketPage", "dojo/domReady!"],
  /**
   * Entry point for ticket page. Hook up BrowserID auth and fetch
   * ticket.
   */
  function (ioq, q, service, browserid, ticketPage) {
    var endLi = q("#metanav .last");
    var target = q("#login-indicator");
    function validate (a) {
      return service.browserIDLogin(a);
    }

    function createLogoutButton(username) {
      var logoutButton = q(document.createElement("li"));
      logoutButton.attr("id", "logout-button");
      logoutButton.attr('innerHTML', '<a href="#">Logout</a>');
      target.attr('innerHTML', "Logged in as " +
                       username + " ");
      logoutButton.insertAfter(target);
      return logoutButton;
    }

    /**
     * Hook up the logout button and store credentials.
     */
    function onLogin(key, username) {
      localStorage.setItem('trac_key', key);
      localStorage.setItem('trac_username',
                           username);
      return createLogoutButton(username);

    };
    /**
     * Display login button and scrub credentials.
     */
    function onLogout() {
      q("#logout-button").remove();
      target.innerHTML("<a href='#'>Login / Register</a>");
      localStorage.removeItem('trac_key');
      localStorage.removeItem('trac_username');
      return target;
    }

    /**
     * Send ticket form data to server.
     */
    function onSubmitChanges(id, data) {
      service.updateTicket(localStorage['trac_key'], id, data)
        .then(function (_) {window.location.reload();},
              ticketPage.renderError);
    }

    var b = browserid(validate, onLogin, onLogout, ticketPage.renderError);
    b.start(localStorage.trac_key,
            localStorage.trac_username,
           function () {
               target.innerHTML("<a href='#'>Login / Register</a>");
               return target;
           });

    var queryString = document.location.search.substr(
      document.location.search[0] === "?" ? 1 : 0);
    var urlQueryArgs = ioq.queryToObject(queryString);
    var d = service.fetchTicket(urlQueryArgs.id);
    d.then(function (r) {ticketPage.renderTicket(r, onSubmitChanges);},
           ticketPage.renderError);
  });