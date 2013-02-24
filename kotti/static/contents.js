$(function() {

    // toggle all checkbox
    $('#toggle-all').change(function(e) {
        $('input[type=checkbox]').attr('checked', $(this).is(':checked'));
    });

    // image preview popovers in contents view
    $('.document-view.content img.thumb').popover({
        html: true,
        trigger: 'hover'
    });

    // drag'n'drop ordering
    $("#contents-table").tableDnD({
        onDrop: function(table, row) {
            var rows = table.tBodies[0].rows;
            var oldPosition = parseInt(row.id, 10);
            var newPosition = parseInt(row.id, 10);
            for (var i=0; i<rows.length; i++) {
                if (parseInt(rows[i].id, 10) == oldPosition) {
                    newPosition = i;
                    break;
                }
            }
            $.post(
                'move-child-position',
                {
                    from: oldPosition,
                    to: newPosition
                },
                function (response) {
                    if (response.result == 'success') {
                        // "renumber" rows on success
                        for (var i=0; i<rows.length; i++) {
                            rows[i].id = i;
                        }
                    } else {
                        // restore old order and show error
                        for (var i=0; i<rows.length; i++) {
                            $("tr#" + i).appendTo("#contents-table tbody");
                        }
                        alert("Reordering not successful, previous order has been restored.");
                    }
                }
            );
        }
    });
});
