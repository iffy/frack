define(
  ["dojo/string", "dojo/_base/query", "dojo/date/locale",
   "frack/mustache",  "frack/groupComments",
   "dojo/text!./resources/ticketbox.html",
   "dojo/text!./resources/changelog.html",
   "dojo/text!./resources/changeticket.html",
   "dojo/NodeList-manipulate"],
  function(string, q, date, Mustache, groupComments, ticketbox, changelog,
           changeticket_form) {
    /** Format a UNIX time as a date. */
    function fromUNIXTime(time) {
      return date.format(new Date(time * 1000));
    }

    /**
     * Find the target DOM node, its corresponding template,
     * and fill the node with the template and data.
     */
    function fill(target, templ, data) {
      var ctempl = Mustache.compile(templ, {"debug": false});
      var rendered = ctempl(data);
      q("#" + target).addContent(rendered);
    }

    return {
      /**
       * Fill templates with data from FetchTicket and display them.
       */
      renderTicket: function (response, onSubmit) {
        q("title").append(
          string.substitute("#${0} (${1}) - Twisted",
                            [response.id, response.summary]));
        response.time = fromUNIXTime(response.time);
        response.changetime = fromUNIXTime(response.changetime);
        fill("ticketbox", ticketbox, response);
        fill("changelog", changelog, {"changes": groupComments(response.changes)});
        if (localStorage.trac_key) {
          response.trac_username = localStorage.trac_username;
          if (response.status == "closed") {
            response.closed = true;
          }
          function submitChangeForm(e) {
            var owner = null;
            var status = null;
            var resolution = null;
            var action = q("input[name='action']").val();
            if (action == 'reopen') {
              status = 'reopened';
            } else if (action == 'resolve') {
              resolution = q("#action_resolve_resolve_resolution").val();
              status = "closed";
            } else if (action == 'reassign') {
              owner = q("#action_reassign_reassign_owner").val();
            }
            var data = {comment: q("#comment").val() || null,
                        summary: q("#field-summary").val(),
                        reporter: q("#field-reporter").val(),
                        description: q("#field-description").val(),
                        type: q("#field-type").val(),
                        priority: q("#field-priority").val(),
                        component: q("#field-component").val(),
                        keywords: q("#field-keywords").val(),
                        cc: q("#field-cc").val(),
                        branch: q("#field-branch").val(),
                        branch_author: q("#field-branch_author").val(),
                        launchpad_bug: q("#field-launchpad_bug").val(),
                        owner: owner,
                        status: status,
                        resolution: resolution
                       };
            onSubmit(response.id, data);
          }
          fill("propertyform", changeticket_form, response);
          q("#propertyform input[name='sumbit']").connect("onclick",
                                                          submitChangeForm);
        }
      },
      /**
       * Show some error text in the page.
       */
      renderError: function displayError(e) {
        var box = q("#errorbox");
        box.addClass("system-message");
        box.text(e);
      }
    };
});