define(["frack/mustache", "dojo/date/locale"], function (Mustache, date) {
         /** Group change entries into comment boxes by author and
          * time. */
         return function groupComments(changes) {
           var commentnum = 1;
           var commentgroups = [];
           var setLineTempl = Mustache.compile(
             "set to <em>{{newvalue}}</em>");
           var changedLineTempl = Mustache.compile(
             "changed from <em>{{oldvalue}}</em> to"
               + " <em>{{newvalue}}</em>");
           changes.forEach(
             function (change) {
               var last = commentgroups[commentgroups.length - 1];
               if (!last || change.author != last.author
                   || change.time != last.unixtime) {
                 last = {"commentnum": commentnum,
                         "time": date.format(new Date(change['time'] * 1000)),
                         "unixtime": change['time'],
                         "author": change['author'], "changes": []};
                 commentgroups.push(last);
                 commentnum += 1;
               }
               if (change.field == 'comment') {
                 last.comment = change.newvalue;
               } else {
                 if (change.field == 'description') {
                   change.changeline = "modified";
                 } else if (!change.oldvalue) {
                   change.changeline = setLineTempl(change);
                 } else if (!change.newvalue) {
                   change.changeline = "removed";
                 } else {
                   change.changeline = changedLineTempl(change);
                 }
                 last.changes.push(change);
               }
             });
           return commentgroups;
         };
});
