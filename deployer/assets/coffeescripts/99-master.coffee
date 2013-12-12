(($) ->
    $('.repeater-remove').prop('disabled', ->
        table = $(this).closest('table')
        size = table.find('> tbody > tr').size()
        repeat_min = parseInt(table.data('repeat-min'))
        return not isNaN(repeat_min) and size <= repeat_min
    )

    $('.repeater-add').prop('disabled', ->
        table = $(this).closest('table')
        size = table.find('> tbody > tr').size()
        repeat_max = parseInt(table.data('repeat-max'))
        return not isNaN(repeat_max) and size >= repeat_max
    )


    $('body').on('click', '.repeater-add', ->
        table = $(this).closest('table')

        repeat_max = parseInt(table.data('repeat-max'))
        repeat_min = parseInt(table.data('repeat-min'))

        size = table.find('> tbody > tr').size()

        if isNaN(repeat_max) or size <= repeat_max
            row = table.find('> tbody > tr:last-child')
            row = row.clone().insertAfter(row)

            # Reset form fields to initial value
            $('input:not([type=checkbox]):not([type=radio]), textarea', row ).val(->
                $(this).prop('defaultValue')
            )
            $('input[type=checkbox], input[type=radio]', row ).prop('checked', ->
                $(this).prop('defaultChecked')
            )
            $('input, textarea', row).eq(0).focus()

        if not isNaN(repeat_max) and size + 1 >= repeat_max
            table.find('.repeater-add').attr('disabled', 'disabled')

        if not isNaN(repeat_min) and size + 1 > repeat_min
            table.find('.repeater-remove').removeAttr('disabled')

                #
        #var field= document.getElementById('field');
        #field.value= field.defaultValue;
    )

    $('body').on('click', '.repeater-remove', ->
        table = $(this).closest('table')

        repeat_max = parseInt(table.data('repeat-max'))
        repeat_min = parseInt(table.data('repeat-min'))

        size = table.find('> tbody > tr').size()

        if isNaN(repeat_min) or size > repeat_min
            $(this).closest('tr').remove()

        if not isNaN(repeat_min) and size - 1 <= repeat_min
            table.find('.repeater-remove').attr('disabled', 'disabled')

        if not isNaN(repeat_max) and size - 1 < repeat_max
            table.find('.repeater-add').removeAttr('disabled')
    )

    $('.key-value-editable').on('submit', ->
        keys = $('.key', this).each(->
            val = $(this).val()
            input = $(this).closest('.form-group').find('.value')
            if val.length
                input.attr('name', val)
            else
                input.removeAttr('name')
        ).map(-> $(this).val()).get().join(',')
        $('<input type="hidden" name="__fields__"/>').val(keys).appendTo(this)
    )

    show_panels_with_errors = (form) ->
        $('.panel-group .panel-collapse.collapse', form).each(->
            if $(this).find('.has-error').size() > 0
                $(this)
                    .collapse('show')
                    .addClass('has-errors')
                    .closest('.panel')
                    .find('a[data-toggle].collapsed')
                    .removeClass('collapsed')
        )

    show_panels_with_errors($('form'))

    $('body').on('submit', 'form.ajaxify', (e) ->
        e.preventDefault()
        form = $(this)
        form.addClass('submitting')
        form.find('[type=submit]').prop('disabled', true)
            .append($("<span/>").addClass('cover'))
            .append($("<span/>").addClass('icon'))
        $.ajax({
            type: form.attr('method'),
            url: form.attr('action'),
            data: form.serialize(),
            success: (data) ->
                if data.status == 'OK'
                    document.location = data.location
                else
                    html = $(data.html)
                    newform = html.find('form.ajaxify')
                    form.replaceWith(newform)
                    show_panels_with_errors(newform)
        })
    )

    $ ->
        $('a.overlay-form').click((e) ->
            e.preventDefault()
            $(this).overlayForm($(this).attr('href'))
        )
)(jQuery)
