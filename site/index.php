<?php
    ini_set('display_errors', 1);
    ini_set('display_startup_errors', 1);
    error_reporting(E_ALL);
    $string = file_get_contents("vmre_db.json");
    $json_a = json_decode($string, true);
?>

<!DOCTYPE html>
<html>
    <head>
        <title>Vancouver Meteor Radar Experiment</title>
        <link rel="stylesheet" href="style.css">
    </head>
    <body>

        <h1>Vancouver Meteor Radar Experiment</h1>

        <a href="https://rasc-vancouver.com/"><img src="rasc-new-banner.png"/></a>

        <p>VMRE is run by members of <a href="https://rasc-vancouver.com/">RASC Vancouver</a>. Confused about what's going on here? <a href="manual.html">This page will help.</a> Have questions? Email me at <a href="mailto:prestonthompson@fastmail.com">prestonthompson@fastmail.com</a></p>

        <p>The source code for VMRE can be found at <a href="https://github.com/preston-thompson/vmre-server">GitHub</a>.</p>

<!--
		<h2>Station status</h2>

        <table>
            <tr>
                <th>Station ID</th>
                <th>Last contact</th>
                <th>Operator</th>
                <th>Location</th>
                <th>Antenna</th>
                <th>Radio</th>
                <th>Computer</th>
            </tr>
% for station_id in stations_last_seen:
            <tr>
                <td>${str(station_id)}</td>
                <td style="background: ${'green' if stations_ok[station_id] else 'red'};">${stations_last_seen[station_id]}</td>
                <td>${config.stations[station_id]["operator"]}</td>
                <td>${config.stations[station_id]["location"]}</td>
                <td>${config.stations[station_id]["antenna"]}</td>
                <td>${config.stations[station_id]["radio"]}</td>
                <td>${config.stations[station_id]["computer"]}</td>
            </tr>
% endfor
        </table>
-->

		<h2>Summary charts</h2>

        <img src="plots/daily.png"><br>
        <img src="plots/timeofday.png">

        <h2>Detections</h2>
        <table>
            <tr>
                <th>Time</th>
                <th>Energy</th>
                <th>Frequency Shift (Hz)</th>
                <th>Velocity (m/s)</th>
            </tr>

            <?php foreach ($json_a['events'] as $event) : ?>
                <tr>
                    <td><a href="plot.php?event=<?=$event['datetime_str']?>"><?=$event['datetime_readable']?></a></td>
                    <td><?=$event['energy']?></td>
                    <td><?=$event['freqshift']?></td>
                    <td><?=$event['velocity']?></td>
                </tr>
            <?php endforeach; ?>
        </table>

    </body>
</html>
