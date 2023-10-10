google.charts.load('current', {'packages': ['corechart']});
google.charts.setOnLoadCallback(drawChart);

function drawChart()
{
    // --- coffee section ---
    var coffee_data = $.ajax({
        url: "coffee_stats",
        dataType: "json",
        async: false
    }).responseJSON;

    if (coffee_data.hasOwnProperty('tod_bins'))
    {
        var data = new google.visualization.DataTable();
        data.addColumn('number', 'time of day');
        data.addColumn('number', 'count');
        for (let i = 0; i < coffee_data.tod_histo.length; i++)
        {
            data.addRow([coffee_data.tod_bins[i], coffee_data.tod_histo[i]]);
        }

        var opts = {'title': 'coffee time of day histogram',
                    'bar': {'groupWidth': "80%"},
                    'chartArea': {'width': '90%', 'height': 'auto'},
                    'legend': {'position': 'bottom'},
                    'width': 800,
                    'height': 480};
        
        var chart = new google.visualization.ColumnChart(document.getElementById('chart_coffee_tod_histo'));
        chart.draw(data, opts);

        var data0 = new google.visualization.DataTable();
        data0.addColumn('date', 'date')
        data0.addColumn('number', 'cups')
        var max_date;
        for (let i = 0; i < coffee_data.daily_count_timeline.length; i++)
        {
            var row = coffee_data.daily_count_timeline[i];
            var date = new Date(row[0])
            data0.addRow([date, row[1]]);

            if (i == coffee_data.daily_count_timeline.length-1)
            {
                max_date = date
            }
        }

        var opts0 = {'title': 'coffee cups count timeline',
                    'hAxis': {'minorGridlines': {'count': 13}, 
                                'gridlines': {'counts': 6},
                                'format': 'dd-MMM'},
                    'lineWidth': 1,
                    'pointSize': 2,  
                    'width': 800,
                    'height': 480,
                    'chartArea': {'width': '90%', 'height': 'auto'},
                    'legend': {'position': 'bottom'},
                    'vAxis': {'textPosition': 'out'},
                    'pointSize': 2,
                    };

        var chart = new google.visualization.LineChart(document.getElementById('chart_coffee_timeline'));
        chart.draw(data0, opts0);

        var data1 = new google.visualization.DataTable();
        data1.addColumn('number', 'bin');
        data1.addColumn('number', 'count');
        for (let i = 0; i < coffee_data.daily_count_histo.length; i++)
        {
        data1.addRow([coffee_data.daily_count_bins[i], coffee_data.daily_count_histo[i]]);
        }

        opts.title = 'coffee cups count histogram';
        var chart = new google.visualization.ColumnChart(document.getElementById('chart_coffee_count_histo'));
        chart.draw(data1, opts);

        document.getElementById('mean_tod').innerHTML = coffee_data.mean_tod;
        document.getElementById('coffee_latest').innerHTML = coffee_data.latest_str;
        document.getElementById('coffee_mean_daily').innerHTML = coffee_data.mean_daily_count.toFixed(2);
        document.getElementById('coffee_cups_today').innerHTML = coffee_data.cups_today;
    }
    else
    {
        document.getElementById('mean_tod').innerHTML = 'No';
        document.getElementById('coffee_latest').innerHTML = 'No';
        document.getElementById('coffee_mean_daily').innerHTML = 'No';
        document.getElementById('coffee_cups_today').innerHTML = 'No';
    }

    // --- sleep section ---
    var sleep_data = $.ajax({
        url: "sleep_stats",
        dataType: "json",
        async: false
    }).responseJSON;

    if (sleep_data.hasOwnProperty('dur_series'))
    {
        // short timeline
        var data = new google.visualization.DataTable();
        data.addColumn('date', 'date');
        data.addColumn('number', 'duration');
        data.addColumn('number', 'deficit');
        var stopdex = sleep_data.dur_series.length - 28;
        if (stopdex < 0)
        {
        stopdex = 0;
        }
        var stop_date = new Date(sleep_data.dur_series[stopdex][0]);
        for (let i = stopdex; i < sleep_data.dur_series.length; i++)
        {
        var row = sleep_data.dur_series[i];
        var date = new Date(row[0]);
        data.addRow([date, row[1], row[2]]);
        }

        var opts = {'title': 'sleep duration timeline (4 weeks)',
                    'width': 800,
                    'height': 480,
                    'lineWidth': 1,
                    'pointSize': 2,
                    'chartArea': {'width': '90%', 'height': 'auto'},
                    'legend': {'position': 'bottom'},
                    'hAxis': {'format': 'dd-MMM',
                            'minValue': stop_date,},
                    'pointSize': 4,
                    };

        var chart = new google.visualization.LineChart(document.getElementById('chart_sleep_dur_short_timeline'));
        chart.draw(data, opts);

        // long timeline
        var data = new google.visualization.DataTable();
        data.addColumn('date', 'date');
        data.addColumn('number', 'duration');
        data.addColumn('number', 'deficit');

        for (let i = 0; i < sleep_data.dur_series.length; i++)
        {
            var row = sleep_data.dur_series[i];
            var date = new Date(row[0]);
            data.addRow([date, row[1], row[2]]);
        }

        opts['title'] = 'sleep duration timeline (26 weeks)'
        opts['pointSize'] = 2;

        var chart = new google.visualization.LineChart(document.getElementById('chart_sleep_dur_timeline'));
        chart.draw(data, opts);

        // mavs
        var data = new google.visualization.DataTable();
        data.addColumn('date', 'date');
        data.addColumn('number', 'mav7');
        data.addColumn('number', 'mav28');

        for (let i = 0; i < sleep_data.dur_series.length; i++)
        {
        var date = new Date(sleep_data.dur_series[i][0]);
        var mav7 = sleep_data.mavs7[i];
        var mav28 = sleep_data.mavs28[i];
        data.addRow([date, mav7, mav28]);
        }

        opts['title'] = 'sleep duration moving average'
        opts['vAxis'] = {'minValue': 0};
        var chart = new google.visualization.LineChart(document.getElementById('chart_sleep_dur_mavs'));
        chart.draw(data, opts);

        // duration histo      
        var data = new google.visualization.DataTable();
        data.addColumn('string', 'duration');
        data.addColumn('number', 'count');

        for (let i = 0; i < sleep_data.dur_histo.length; i++)
        {
        data.addRow([sleep_data.dur_bins[i], sleep_data.dur_histo[i]]);
        }
        var opts1 = {'title': 'sleep duration histogram',
                    'bar': {'groupWidth': "90%"},
                    'hAxis': {'showTextEvery': 4,
                            //   'slantedText': true,
                            //   'slantedTextAngle': 90,
                            },
                    'chartArea': {'width': '90%', 'height': 'auto'},
                    'legend': {'position': 'bottom'},
                    'width': 800,
                    'height': 480};
        var chart = new google.visualization.ColumnChart(document.getElementById('chart_sleep_dur_histo'));
        chart.draw(data, opts1);

        // sleep wake histo
        var data = new google.visualization.DataTable();
        data.addColumn('string', 'time-of-day');
        data.addColumn('number', 'wake');
        data.addColumn('number', 'sleep');
        for (let i = 0; i < sleep_data.wake_histo.length; i++)
        {
        data.addRow([sleep_data.wake_bins[i], sleep_data.wake_histo[i], sleep_data.sleep_histo[i]]);
        }
        opts1['title'] = 'sleep-wake time histogram';
        opts1.isStacked = true;
        
        var chart = new google.visualization.ColumnChart(document.getElementById('chart_sleep_wake_histo'));
        chart.draw(data, opts1);

        // simple values
        document.getElementById('sleep_latest').innerHTML = sleep_data.latest_str;
        document.getElementById('sleep_latest_dur').innerHTML = sleep_data.latest_dur.toFixed(2);
        document.getElementById('sleep_semester_mean').innerHTML = sleep_data.semester_mean.toFixed(2);
        document.getElementById('sleep_last_week_mean').innerHTML = sleep_data.last_week_mean.toFixed(2);
        document.getElementById('sleep_week_deficit').innerHTML = sleep_data.week_deficit.toFixed(2);
    }
    else
    {
        document.getElementById('sleep_latest').innerHTML = 'No';
        document.getElementById('sleep_latest_dur').innerHTML = 'No';
        document.getElementById('sleep_semester_mean').innerHTML = 'No';
        document.getElementById('sleep_last_week_mean').innerHTML = 'No';
        document.getElementById('sleep_week_deficit').innerHTML = 'No';
    }

    // --- meal section ---
    var meal_data = $.ajax({
        url: "meal_stats",
        dataType: "json",
        async: false
    }).responseJSON;

    if (meal_data.hasOwnProperty('time_bins'))
    {
        // time histo
        var data = new google.visualization.DataTable();
        data.addColumn('string', 'time-of-day');
        data.addColumn('number', 'breakfast');
        data.addColumn('number', 'lunch');
        data.addColumn('number', 'dinner');
        for (let i = 0; i < meal_data.breakfast_histo.length; i++)
        {
            data.addRow([meal_data.time_bins[i], meal_data.breakfast_histo[i], meal_data.lunch_histo[i], meal_data.dinner_histo[i]]);
        }

        opts1.title = 'meal time histogram';
        var chart = new google.visualization.ColumnChart(document.getElementById('chart_meal_histo'));
        chart.draw(data, opts1);

        document.getElementById("meals_latests").innerHTML = meal_data.latest_str;
    }
    else
    {
        document.getElementById("meals_latests").innerHTML = 'No';
    }

    // --- shower section ---
    var shower_data = $.ajax({
    url: "shower_stats",
    dataType: "json",
    async: false
    }).responseJSON;

    if (shower_data.hasOwnProperty('t_bins'))
    {
        // time histo
        var data = new google.visualization.DataTable();
        data.addColumn('string', 'time-of-day');
        data.addColumn('number', 'count')
        for (let i = 0; i < shower_data.t_histo.length; i++)
        {
            data.addRow([shower_data.t_bins[i], shower_data.t_histo[i]]);
        }

        opts1.title = 'shower time histogram';
        var chart = new google.visualization.ColumnChart(document.getElementById('chart_shower_t_histo'));
        chart.draw(data, opts1);

        // interval histo
        var data = new google.visualization.DataTable();
        data.addColumn('string', 'interval');
        data.addColumn('number', 'count');
        for (let i = 0; i < shower_data.dt_histo.length; i++)
        {
            data.addRow([shower_data.dt_bins[i], shower_data.dt_histo[i]]);
        }

        opts1.title = 'shower interval histogram';
        var chart = new google.visualization.ColumnChart(document.getElementById('chart_shower_dt_histo'));
        chart.draw(data, opts1);

        document.getElementById('shower_latest').innerHTML = shower_data.latest;
        document.getElementById('shower_mean_interval').innerHTML = shower_data.mean_dt;
    }
    else
    {
        document.getElementById('shower_latest').innerHTML = 'No';
        document.getElementById('shower_mean_interval').innerHTML = 'No';
    }

}