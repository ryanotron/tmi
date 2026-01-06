google.charts.load('current', {'packages': ['corechart']});
google.charts.setOnLoadCallback(drawChart);

function drawChart()
{
    // get activity name
    const params = new URLSearchParams(window.location.search)
    const actname = params.get('name')
    console.log(actname)
    if (actname == null)
        return;

    var act_data = $.ajax({
    url: `activity_stats?name=${actname}`,
    dataType: "json",
    async: false
    }).responseJSON;

    if (act_data.hasOwnProperty('t_bins'))
    {
        // chart option
        var opts1 = {'title': 'placeholder',
            'bar': {'groupWidth': "90%"},
            'hAxis': {'showTextEvery': 4,
                    //   'slantedText': true,
                    //   'slantedTextAngle': 90,
                    },
            'chartArea': {'width': '90%', 'height': 'auto'},
            'legend': {'position': 'bottom'},
            'width': 800,
            'height': 480};

        // time histo
        var data = new google.visualization.DataTable();
        data.addColumn('string', 'time-of-day');
        data.addColumn('number', 'count')
        for (let i = 0; i < act_data.t_histo.length; i++)
        {
            data.addRow([act_data.t_bins[i], act_data.t_histo[i]]);
        }

        opts1.title = `${actname} time histogram`;
        var chart = new google.visualization.ColumnChart(document.getElementById('chart_t_histo'));
        chart.draw(data, opts1);

        // interval histo
        var data = new google.visualization.DataTable();
        data.addColumn('string', 'interval');
        data.addColumn('number', 'count');
        for (let i = 0; i < act_data.dt_histo.length; i++)
        {
            data.addRow([act_data.dt_bins[i], act_data.dt_histo[i]]);
        }

        opts1.title = `${actname} interval histogram`;
        var chart = new google.visualization.ColumnChart(document.getElementById('chart_dt_histo'));
        chart.draw(data, opts1);

        document.getElementById('latest').innerHTML = act_data.latest;
        document.getElementById('mean_interval').innerHTML = act_data.mean_dt;
    }
    else
    {
        document.getElementById('latest').innerHTML = 'No';
        document.getElementById('mean_interval').innerHTML = 'No';
    }
}