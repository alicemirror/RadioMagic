/**
 * \file html_radiohome.h
 * \brief Definition of the home page of RadioMagic
 */
#ifndef _RADIOHOME
#define _RADIOHOME
const char MAIN_page[] PROGMEM = R"=====(
<!DOCTYPE html>
<html>
<style>
body {
  text-align:center;
  font-family: helvetica;
}
canvas {
  border: 2px solid rgb(151, 149, 149);
}
</style>
<body>
Balearic Dynamics Web Server
<h1>Radio Magic</h1>
<h3>Main Page</h3>
<canvas id="stage" height="400" width="520"></canvas><br>
</body>
</html>
)=====";
#endif
