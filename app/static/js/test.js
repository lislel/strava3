//(function($) {
//    var since = 0;
//    setInterval(function() {
//    $.ajax('{{ url_for('main.notifications') }}?since=' + since).done(
//    function(notifications) {
//        for (var i = 0; i < notifications.length; i++) {
//            set_task_progress(notifications[i].data.task_id,
//            notifications[i].data.progress;
//        }
//            since = notifications[i].timestamp;
//    }
//    });
//            }, 10000)(jQuery); // End of use strict
function set_task_progress(task_id, progress) {
    $('#' + task_id + '-progress').text(progress);
    }

$(function() {
    var since = 0;
    setInterval(function() {
        $.ajax('{{ url_for('main.notifications') }}?since=' + since).done(
            function(notifications) {
                for (var i = 0; i < notifications.length; i++) {
                    set_task_progress(notifications[i].data.task_id, notifications[i].data.progress);
                    since = notifications[i].timestamp;
                }
            }
        );
    }, 10000);
});
(jQuery); // End of use strict