require(
  ["doh/runner", "dojo/_base/query", "dojo/_base/Deferred", "frack/browserid"],
  function (doh, q, Deferred, browserid) {
    var _unpatchers = [];
    function patch(target, name, fake) {
      var original = target[name];
      _unpatchers.push(function() {target[name] = original;});
      target[name] = fake;
    }
    function unpatchAll() {
      _unpatchers.forEach(function (x) {x();});
      _unpatchers = [];
    }
    doh.register("browserid",
     [{name: "loginSuccess",
       runTest: function (self) {
         var fakeAssertion = {
           fake_assertion: "data"
         };
         var fakeValidationResponse = {
           ok: true,
           otherkey: "othervalue"
         };
         var visited = [];
         var b = browserid(
           function validateAssertion(a) {
             self.assertEqual(a, fakeAssertion);
             visited.push("validate");
             var d = new Deferred();
             d.callback(fakeValidationResponse);
             return d;
           },
           function onLogin(response) {
             visited.push("login");
             self.assertEqual(response, fakeValidationResponse);
             return q(document.createElement("div"));
           },
           function onLogout() {
             visited.push("logout");
             return q(document.createElement("div"));
           },
           null);
         patch(navigator.id, "get",
               function(f, opts) {
                 visited.push("browserid");
                 self.assertEqual(opts, {silent: true}, "opts");
                 f(fakeAssertion);
               });
         b.start();
         self.assertEqual(visited, ["browserid", "validate", "login"]);
       },
       tearDown: unpatchAll
      },
      {name: "validateFailure",
       runTest: function (self) {
         var visited = [];
         var err = "broken";
         var b = browserid(
           function validateAssertion(a) {
             visited.push("validate");
             throw err;
           },
           null, null,
           function handleError(e) {
             visited.push("error");
             self.assertEqual(e, err);
           });
         patch(navigator.id, "get",
               function(f, opts) {
                 visited.push("browserid");
                 self.assertEqual(opts, {silent: true}, "opts");
                 f("foo");
               });
         b.start();
         self.assertEqual(visited, ["browserid", "validate", "error"]);
       },
       tearDown: unpatchAll
      }
     ]);
  });