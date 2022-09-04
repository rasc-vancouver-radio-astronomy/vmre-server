<?php
    ini_set('display_errors', 1);
    ini_set('display_startup_errors', 1);
    error_reporting(E_ALL);
    $string = file_get_contents("vmre_db.json");
    $json_a = json_decode($string, true);
    $event_datetime_str = $_GET['event'];
    $event = $json_a['events'][$event_datetime_str];
?>

<!DOCTYPE html>
<html>
    <head>
        <title><?=$event['datetime_readable']?></title>
        <link rel="stylesheet" href="style.css">
    </head>

    <body>
        <h1><a href="index.php">Main page</a></h1>
<!--
        <table>
            <tr>
                <td><h1>
% if prev_event is not None:
                    <a href="${prev_event['datetime_str']}.html">Prev</a><br>
% else:
                    Prev
% endif
                </h1></td>
                <td><h1>
                    <a href="index.html">Home</a><br>
                </h1></td>
                <td><h1>
% if next_event is not None:
                    <a href="${next_event['datetime_str']}.html">Next</a><br>
% else:
                    Next
% endif
                </h1></td>
            </tr>
        </table>
-->

        <?php foreach ($event['plots'] as $plot) : ?>
            <img src="<?=$plot?>">
        <?php endforeach; ?>

        <br>

        <table>
            <tr>
                <td>Energy</td>
                <td><?=$event['energy']?></td>
            </tr>
            <tr>
                <td>Frequency Shift (Hz)</td>
                <td><?=$event['freqshift']?></td>
            </tr>
            <tr>
                <td>Velocity (m/s)</td>
                <td><?=$event['velocity']?></td>
            </tr>
        </table>

        <p>Confused about what's going on here? <a href="manual.html">This page will help.</a></p>

    </body>
</html>
