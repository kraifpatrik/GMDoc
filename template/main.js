$(function () {
  const active = $('#side-menu').find('a.active')[0];
  if (active) {
    active.scrollIntoView();
  }

  if ($(window).width() < 1024) {
    $('#side-menu').toggle();
  }

  $('#btn-menu-toggler').click(function () {
    $('#side-menu').toggle();
  });

  $('#side-menu').find('i[data-target]').each(function (i, e) {
    const self = $(e);
    self.on('click', function () {
      if (self.hasClass('fa-minus-square')) {
        self.removeClass('fa-minus-square').addClass('fa-plus-square');
      } else if (self.hasClass('fa-plus-square')) {
        self.removeClass('fa-plus-square').addClass('fa-minus-square');
      }
      const target = self.attr('data-target');
      $(target).toggle();
    });
  });

  $('[data-like]').on('click', function () {
    $('input[name="like"]').val(parseInt($(this).attr('data-like')));
  });

  $('.char-count').each(function () {
    const self = $(this);
    $(self.attr('data-target')).on('change input', function () {
      self.text($(this).val().length);
    });
  });

  $('#form-rating').on('submit', function (e) {
    e.preventDefault();
    const formData = new FormData(this);
    formData.append("page", window.location);

    const btnSubmit = $(this).find('button[type="submit"]');

    $.ajax({
      url: $(this).attr('action'),
      method: $(this).attr('method'),
      data: formData,
      processData: false,
      contentType: false,
      success: function () {
        btnSubmit.removeClass('btn-primary')
          .removeClass('btn-danger')
          .addClass('btn-success');

        btnSubmit.find('.far')
          .removeClass('fa-circle')
          .removeClass('fa-times-circle')
          .addClass('fa-check-circle');

        setTimeout(function () {
          $('#mod-rating').modal('hide');
          $('#rating').hide();
        }, 250);
      },
      error: function () {
        btnSubmit.removeClass('btn-primary')
          .removeClass('btn-success')
          .addClass('btn-danger');

        btnSubmit.find('.far')
          .removeClass('fa-circle')
          .removeClass('fa-check-circle')
          .addClass('fa-times-circle');
      }
    });

  });
});