function setProgressBar(current, total, message)
{
  progress = (current == 0)? 0 : Math.ceil(current / total * 100);
  $("#progress-bar").css("width", progress + "%");
  $("#progress-bar").html(progress + "%");
  if (message) {
    $("#progress-bar-status").html(message);
  }
}

function setProgressMessage(message) {
  if (message) {
    $("#progress-message").html(message);
  } else {
    $("#progress-message").html("&nbsp;");
  }
}

function flash(message, category)
{
  $("#form").before('<div class="alert alert-' + category + '" role="alert">' + message + '</div>');
  setTimeout(function() {
    $(".alert-info, .alert-success, .alert-primary, .alert-warning").fadeTo(1000, 0).slideUp(1000, function(){
      $(this).remove();
    });
  }, 5000);
}

$(document).ready(function() {
  $("#button-clear-keywords").click(function() {
    $("#keywords").val('');
  });

  $("#button-clear-countries").click(function() {
    $("#countries option:selected").prop("selected", false);
  });
});