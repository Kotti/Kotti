// JSLint options:
/*global $, alert*/

"use strict";
$(function () {

    // toggle all checkbox
    $('#toggle-all').change(function () {
        $('input[type=checkbox]').prop('checked', this.checked);
    });

    // image preview popovers in contents view
    $('.document-view.content img.thumb').popover({
        html: true,
        trigger: 'hover'
    });

    // drag'n'drop ordering
    $("#contents-table").tableDnD({
        onDrop: function (table, row) {
            var rows = table.tBodies[0].rows,
                oldPosition = parseInt(row.id, 10),
                newPosition = parseInt(row.id, 10),
                i;
            for (i = 0; i < rows.length; i += 1) {
                if (parseInt(rows[i].id, 10) === oldPosition) {
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
                    if (response.result === 'success') {
                        // "renumber" rows on success
                        for (i = 0; i < rows.length; i += 1) {
                            rows[i].id = i;
                        }
                    } else {
                        // restore old order and show error
                        for (i = 0; i < rows.length; i += 1) {
                            $("tr#" + i).appendTo("#contents-table tbody");
                        }
                        alert("Reordering was not successful. Previous order has been restored.");
                    }
                }
            );
        }
    });
});
