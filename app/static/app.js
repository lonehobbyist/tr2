$(document).ready(function() {
    $('#nifty-form').submit(function(event) {
        event.preventDefault();
        const startDate = $('#start-date').val();
        const endDate = $('#end-date').val();
        $.ajax({
            url: '/download_nifty_data',
            method: 'POST',
            contentType: 'application/json',
            data: JSON.stringify({ start_date: startDate, end_date: endDate }),
            success: function(response) {
                console.log(response);
                alert(response.message);
            },
            error: function(error) {
                console.error(error);
                alert('Error downloading NIFTY50 data.');
            }
        });
    });

    $('#options-form').submit(function(event) {
        event.preventDefault();
        const startDate = $('#start-date').val();
        const endDate = $('#end-date').val();
        const optionsSymbols = $('#options-symbols').val().split(',').map(s => s.trim());
        $('#progress-container').show();
        let completed = 0;
        optionsSymbols.forEach(symbol => {
            $.ajax({
                url: '/download_options_data',
                method: 'POST',
                contentType: 'application/json',
                data: JSON.stringify({ symbol: symbol, start_date: startDate, end_date: endDate }),
                success: function(response) {
                    console.log(response);
                    completed++;
                    const progress = (completed / optionsSymbols.length) * 100;
                    $('#progress-bar').css('width', progress + '%').text(Math.round(progress) + '%');
                    if (completed === optionsSymbols.length) {
                        alert('Options data downloaded successfully.');
                        $('#progress-container').hide();
                        fetchSignals();
                    }
                },
                error: function(error) {
                    console.error(error);
                    alert('Error downloading options data for ' + symbol);
                }
            });
        });
    });

    function fetchSignals() {
        $.ajax({
            url: '/get_signals',
            method: 'GET',
            success: function(response) {
                console.log(response);
                $('#signals-container').show();
                const signalsList = $('#signals-list');
                signalsList.empty();
                response.signals.forEach(signal => {
                    signalsList.append('<li class="list-group-item">' + signal + '</li>');
                });
            },
            error: function(error) {
                console.error(error);
                alert('Error fetching signals.');
            }
        });
    }
});
