class CustomReporter:

    @staticmethod
    def get_custom_monkey_html_template():
        return """
                    <!DOCTYPE html>
                    <html lang="en">
                        <head>
                            <link rel="icon" href="">
                            <meta charset="UTF-8">
                            <title>QA automation Report</title>
                            <script src="https://code.jquery.com/jquery-3.3.1.min.js"
                                    integrity="sha256-FgpCb/KJQlLNfOu91ta32o/NMZxltwRo8QtmkMRdAu8="
                                    crossorigin="anonymous"></script>
                            <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/2.7.3/Chart.bundle.min.js"></script>
                            <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/materialize/0.100.2/css/materialize.min.css">
                            <script src="https://cdnjs.cloudflare.com/ajax/libs/materialize/0.100.2/js/materialize.min.js"></script>
                            <link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">
                            <link href="https://cdn.datatables.net/1.10.19/css/jquery.dataTables.min.css" rel="stylesheet">
                            <link rel="stylesheet" href="https://use.fontawesome.com/releases/v5.7.2/css/all.css" integrity="sha384-fnmOCqbTlWIlj8LyTjo7mOUStjsKC4pOpQbqyi7RrhN7udi9RwhKkMHpvLbHG9Sr" crossorigin="anonymous">
                            <script src="https://www.amcharts.com/lib/4/core.js"></script>
                            <script src="https://www.amcharts.com/lib/4/charts.js"></script>
                            <script src="https://www.amcharts.com/lib/4/themes/dark.js"></script>
                            <script src="https://www.amcharts.com/lib/4/themes/animated.js"></script>
                            <script src="https://cdn.datatables.net/1.10.19/js/jquery.dataTables.min.js"></script>
                        </head>
                         <div>
                          <a href="https://qa-automation.omnilatam.com" class="modal-close waves-effect waves-green btn-flat card-content white-text back-button"> ❮ Previous </a>
                        <script async defer src="https://buttons.github.io/buttons.js"></script>
                    </div>
                        <body style="background-color: #3d4f58;">
                            <style>
                                .back-button{{
                                    background-color: #3d4f58;
                                    border: 1px solid white;
                                    border-radius: 12px;
                                    margin: 10px;
                                }}
                                .back-button:hover{{
                                    background-color: white;
                                    color: #3d4f58 !important;
                                }}
                                .absolute_cards{{
                                    min-height: 170px;
                                    overflow: hidden;
                                }}

                                .absolute_value{{
                                    font-size: 27px;
                                }}

                                .modal_absolute_value{{
                                    font-size: 17px;
                                }}

                                .card:hover {{
                                    background: #193746 !important;
                                    transition: all .3s ease-in;
                                }}

                                body {{
                                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol";
                                }}

                                .success {{
                                    background: #12d479;
                                }}
                                .fail {{
                                    background: #fcd75f;
                                }}
                                .error {{
                                    background: #ff7651;
                                }}
                                .ignore {{
                                    background: #cce4eb;
                                }}
                                .skip {{
                                    background: #34bff5;
                                }}
                                .cancel {{
                                    background: #f19def;
                                }}
                                .info-badge {{
                                    background: #aac7d2;
                                }}

                                .parent-badge{{
                                    margin-top: 8px;
                                }}

                                .badge {{
                                    border-radius: 3px;
                                    margin-right: 7px;
                                    color: #333 !important;
                                }}

                                .traceback {{
                                    background: #23323a !important;
                                    padding: 15px !important;
                                    color: #fd5858 !important;
                                    margin: 0px !important;
                                }}

                                .collapsible-header {{
                                    background: #37474f !important;
                                    border-color: #193746;
                                }}

                                .collapsible.expandable {{
                                    border: 1px #37474f;
                                }}

                                .collapsible-header:hover {{
                                    background: #193746 !important;
                                    transition: all .3s ease-in;
                                    transition: all .3s ease-out;
                                }}

                                .collapsible-body {{
                                    border-color: transparent;
                                }}

                                .attempt-header {{
                                    padding: 5px;
                                    padding-bottom: 0px;
                                    border: 0px;
                                }}

                                .parameter {{
                                  white-space: nowrap;
                                  overflow: hidden;
                                  text-overflow: ellipsis;
                                  font-size: 14px;
                                }}

                                html {{
                                    overflow: scroll;
                                    overflow-x: hidden;
                                }}
                                ::-webkit-scrollbar {{
                                    width: 0px;  /* remove scrollbar space */
                                    background: transparent;  /* optional: just make scrollbar invisible */
                                }}
                                /* optional: show position indicator in red */
                                ::-webkit-scrollbar-thumb {{
                                    background: transparent;
                                }}
                                .traceback > textarea{{
                                    padding-bottom: 0px;
                                    margin-bottom: 0px;
                                    overflow: auto;
                                }}
                                .large-data-card{{
                                    width: 100%;
                                    height: 370px;
                                }}
                            </style>
                            {body}
                            <script>
                                var database_lol = {database_lol}
                                function registerCopy(){{
                                    $(".copy_icon").on("click", function(event){{
                                        event.stopPropagation();
                                        var copy_target = event.target.dataset.tcopy
                                        var data_element = document.getElementById(copy_target);
                                        if(data_element.tagName == "textarea") var val = data_element.value
                                        else var val = data_element.innerHTML

                                        var $temp = $("<input>");
                                        $("body").append($temp);
                                        $temp.val(val).select();
                                        document.execCommand("copy");
                                        $temp.remove();

                                        Materialize.toast('Copied!', 2000)
                                    }});
                                }};
                            </script>
                        </body>
                    </html> 
                   """
