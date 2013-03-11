define(
  ["dojo/rpc/JsonService"],
  /**
   * JSON-RPC request methods.
   */
  function (makeService, baseUrl) {
    var frack = makeService({"serviceUrl": "../amp"});
    return {
      fetchTicket: function (id) {
        frack.timeout = 30000;
        return frack.callRemote("FetchTicket",
                                {"id": Number(id),
                                 "asHTML": true});
      },
      browserIDLogin: function (assertion) {
        frack.timeout = 300000;
        return frack.callRemote("BrowserIDLogin",
                                {"assertion": assertion});
      },

      updateTicket: function (key, ticketid, data) {
        frack.timeout = 30000;
        data.id = ticketid;
        data.key = key;
        return frack.callRemote("UpdateTicket", data);
      }
    };
  });