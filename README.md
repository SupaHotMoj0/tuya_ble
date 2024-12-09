<h1 align="center">Work in Progress:<br>Tuya BLE Devices</h1>

<p align="center">
  <img src="https://img.shields.io/github/license/SupaHotMoj0/tuya_ble?style=flat-square" alt="License">
  <img src="https://img.shields.io/github/stars/SupaHotMoj0/tuya_ble?style=flat-square" alt="Stars">
  <img src="https://img.shields.io/github/forks/SupaHotMoj0/tuya_ble?style=flat-square" alt="Forks">
</p>

<h2 align="center">Overview</h2>
<p align="center">
  This integration allows you to integrate and control Tuya BLE (Bluetooth Low Energy) devices directly within Home Assistant,
  enabling local operations without relying on remote cloud services for core functionality.
</p>
<p align="center">
  Inspired by and derived from the code of:
  <a href="https://github.com/PlusPlus-ua/ha_tuya_ble">@PlusPlus-u</a> and 
  <a href="https://github.com/redphx/poc-tuya-ble-fingerbot">@redphx</a>.
</p>

<h2 align="center">Features</h2>
<p align="center">
  • Automatic or manual discovery of supported Tuya BLE devices <br>
  • Local control and status reporting <br>
  • Support for multiple device categories and models <br>
  • No cloud round-trip for commands once the device credentials are obtained
</p>

<h2 align="center">Installation</h2>
<p align="center">
  To install, place the <code>custom_components</code> folder into your Home Assistant configuration directory.
  Alternatively, you can install via <a href="https://hacs.xyz/">HACS</a>.
</p>
<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=SupaHotMoj0&repository=tuya_ble&category=integration">
    <img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="HACS">
  </a>
</p>

<h2 align="center">Configuration & Setup</h2>
<p align="center">
  Once installed, the integration attempts to automatically discover all supported Bluetooth devices.
  If needed, you can also add discoverable devices manually through the Home Assistant UI.
</p>
<p align="center">
  <b>Note:</b> Although this integration works locally, you must provide a device ID and encryption key for each Tuya BLE device.
  These credentials are the same as those used by the official Tuya integration and can be obtained from the Tuya IoT platform.
  For detailed instructions, please refer to the official <a href="https://www.home-assistant.io/integrations/tuya/">Tuya integration documentation</a>.
</p>

<h2 align="center">Supported Devices</h2>
<p align="center">
  Below is a list of currently supported device categories and their corresponding products.
</p>

<h3>Fingerbots (Category ID: 'szjqr')</h3>
<ul>
  <li>Fingerbot (Product IDs: 'ltak7e1p', 'y6kttvd6', 'yrnk7mnn', 'nvr2rocq', 'bnt7wajf', 'rvdceqjh', '5xhbk964'): 
    The original CR2 battery-powered device.</li>
  <li>Adaprox Fingerbot (Product ID: 'y6kttvd6'): 
    Similar to the original Fingerbot, featuring a built-in battery with USB-C charging.</li>
  <li>Fingerbot Plus (Product IDs: 'blliqpsj', 'ndvkgsrm', 'yiihr7zh', 'neq16kgd'): 
    An enhanced Fingerbot with a sensor button for manual control.</li>
  <li>CubeTouch 1s (Product ID: '3yqdo5yt'): 
    A variant with a built-in battery and USB-C charging.</li>
  <li>CubeTouch II (Product ID: 'xhf790if'): 
    Another variant featuring a built-in battery and USB-C charging.</li>
</ul>

<p>All Fingerbot variants are fully integrated into Home Assistant. The Fingerbot Plus offers programmable actions (series of custom commands) exposed as Home Assistant entities. These include:</p>
<ul>
  <li><b>Program (switch):</b> Activate or deactivate a custom sequence.</li>
  <li><b>Repeat forever (boolean):</b> Loop the programmed sequence indefinitely.</li>
  <li><b>Repeats count (number):</b> Define how many times the sequence repeats.</li>
  <li><b>Idle position (slider):</b> Set the default idle position percentage.</li>
  <li><b>Program (text):</b> Define the sequence of actions. Format: <code>position[/time];...</code> 
    where <code>position</code> is in percentages and <code>time</code> is in seconds (0 if omitted).</li>
</ul>

<h3>Temperature and Humidity Sensors (Category ID: 'wsdcg')</h3>
<ul>
  <li>Soil Moisture Sensor (Product ID: 'ojzlzzsw')</li>
</ul>

<h3>CO2 Sensors (Category ID: 'co2bj')</h3>
<ul>
  <li>CO2 Detector (Product ID: '59s19z5m')</li>
</ul>

<h3>Smart Locks (Category ID: 'ms')</h3>
<ul>
  <li>Smart Lock (Product IDs: 'ludzroix', 'isk2p555')</li>
</ul>

<h3>Climate (Category ID: 'wk')</h3>
<ul>
  <li>Thermostatic Radiator Valve (Product IDs: 'drlajpqc', 'nhj2j7su')</li>
</ul>

<h3>Smart Water Bottle (Category ID: 'znhsb')</h3>
<ul>
  <li>Smart Water Bottle (Product ID: 'cdlandip')</li>
</ul>

<h3>Irrigation Computer (Category ID: 'ggq')</h3>
<ul>
  <li>Irrigation Computer (Product ID: '6pahkcau')</li>
</ul>

<h2 align="center">Additional Notes</h2>
<p align="center">
  This integration is a work-in-progress. More devices, categories, and features are planned.
</p>

<h2 align="center">Contributing</h2>
<p align="center">
  Contributions are welcome! If you encounter issues or have suggestions for enhancements, please open an issue or create a pull request.
</p>

<h2 align="center">License</h2>
<p align="center">
  This project is licensed under the MIT License. See the <a href="LICENSE">LICENSE</a> file for details.
</p>
