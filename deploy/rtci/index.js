function customizeDataTable(settings, json) {
  console.log("customizeDataTable called");  // Debug message
  $(this.api().table().header()).css({'background-color': '#2d5ef9', 'color': '#ffffff'});
  $('.dataTables_wrapper').find('label').each(function() {
    $(this).css('color', '#ffffff');
  });
  $('.dataTables_wrapper').find('.dataTables_info').css('color', '#ffffff');
  $('.dataTables_wrapper').find('.paginate_button').css('color', '#ffffff');
  $('.dataTables_wrapper').find('table').css('color', '#ffffff');
  $('.paginate_button').not('.current').hover(function() {
    $(this).css('color', '#2d5ef9').css('background-color', '#ffffff');
  }, function() {
    $(this).css('color', '#ffffff').css('background-color', '');
  });
}
