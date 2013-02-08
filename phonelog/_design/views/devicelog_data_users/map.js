function(doc) {
    if (doc.xmlns == 'http://code.javarosa.org/devicereport') {
        for (var i in doc.form.log_subreport.log) {
            var entry = doc.form.log_subreport.log[i];
            if (entry.type == 'login') {
                var user = entry.msg.substring(entry.msg.indexOf('-') + 1);
                emit([doc.domain, user], null);
            }
        }
        if (doc.form.user_subreport) {
            for (var i in doc.form.user_subreport.user) {
                var username = doc.form.user_subreport.user[i].username;
                emit([doc.domain, username], null);
            }
        }
    }
}
