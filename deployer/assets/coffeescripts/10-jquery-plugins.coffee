(($) ->
    overlay_padding = 60

    getOverlay = ->
        overlay = $('#overlay')
        if not overlay.size()
            overlay = $('<div id="overlay"></div>')
            $('body').keydown((e) ->
                switch e.which
                    when 27
                        closeOverlay()
            ).append(overlay)
        return overlay

    closeOverlay = ->
        getOverlay().remove()

    showInOverlay = (el) ->
        overlay = getOverlay().empty().append(el)
        repositionOverlayContent(overlay, el)

    repositionOverlayContent = (overlay, el) ->
        m = Math.max((overlay.outerHeight() - el.outerHeight()) / 2 - overlay_padding - 60, 0)
        el.css('margin-top', "#{m}px")

    formSubmit = (e) ->
        e.preventDefault()
        container = $(this)
        form = container.find('form')
        form.addClass('submitting')
        form.find('[type=submit]').prop('disabled', true)
            .append($("<span/>").addClass('cover'))
            .append($("<span/>").addClass('icon'))
        url = form.attr('action')
        $.ajax({
            type: form.attr('method'),
            url: url,
            data: form.serialize(),
            success: (data) ->
                if data.status == 'OK'
                    document.location = data.location
                else
                    showForm($(data.html), url)
        })

    showForm = (html, url) ->
        html.submit(formSubmit)
        html.find('form').attr('action', (i, val) ->
            return val or url
        )
        html.find('[data-action=cancel]').click((e) ->
            e.preventDefault()
            closeOverlay()
        )
        showInOverlay(html)

    $.fn.overlayForm = (url) ->
        overlay = getOverlay()
        $.ajax(url, {
            success: (data) ->
                showForm($(data), url)
        })
)(jQuery)
