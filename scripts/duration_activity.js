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

    // --- get data section ---
    var act_data = $.ajax({
        url: `duration_activity_stats?name=${actname}`,
        dataType: "json",
        async: false
    }).responseJSON;

    if (act_data.hasOwnProperty('t_bins'))
    {
        // duration histo      
        var data = new google.visualization.DataTable();
        data.addColumn('string', 'duration');
        data.addColumn('number', 'count');

        for (let i = 0; i < act_data.dur_histo.length; i++)
        {
            data.addRow([act_data.dur_bins[i], act_data.dur_histo[i]]);
        }

        var opts1 = {'title': `${actname} duration histogram`,
                     'bar': {'groupWidth': "90%"},
                     'hAxis': {'showTextEvery': 4,
                             //   'slantedText': true,
                             //   'slantedTextAngle': 90,
                             },
                     'chartArea': {'width': '90%', 'height': 'auto'},
                     'legend': {'position': 'bottom'},
                     'width': 800,
                     'height': 480};
        var chart = new google.visualization.ColumnChart(document.getElementById('chart_act_dur_histo'));
        chart.draw(data, opts1);

        // begin/end histo
        var data = new google.visualization.DataTable();
        data.addColumn('string', 'time-of-day');
        data.addColumn('number', 'begin');
        data.addColumn('number', 'end');
        for (let i = 0; i < act_data.t_begin_histo.length; i++)
        {
            data.addRow([act_data.t_bins[i], act_data.t_begin_histo[i], act_data.t_end_histo[i]]);
        }
        opts1['title'] = 'begin/end time histogram';
        // opts1.isStacked = true;
        
        var chart = new google.visualization.ColumnChart(document.getElementById('chart_act_begin_histo'));
        chart.draw(data, opts1);
    }
    else
    {
        document.getElementById('act_latest').innerHTML = 'No';
        document.getElementById('act_latest_dur').innerHTML = 'No';
    }
}