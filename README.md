<h1 align="center">Work in Progress: <br>Tuya BLE Devices</h1>

<p align="center">
  <img src="https://img.shields.io/github/license/SupaHotMoj0/tuya_ble?style=flat-square" alt="License">
  <img src="https://img.shields.io/github/stars/SupaHotMoj0/tuya_ble?style=flat-square" alt="Stars">
  <img src="https://img.shields.io/github/forks/SupaHotMoj0/tuya_ble?style=flat-square" alt="Forks">
</p>

<h2 align="center">Overview</h2>

<p align="center">
  This integration supports Tuya devices connected via BLE.
</p>
<p align="center">
  Inspired by the code of <a href="https://github.com/PlusPlus-ua/ha_tuya_ble">@PlusPlus-u</a> and <a href="https://github.com/redphx/poc-tuya-ble-fingerbot">@redphx</a>.
</p>

<h2 align="center">Installation</h2>

<p align="center">
  To install, place the <code>custom_components</code> folder in your Home Assistant configuration directory. <br>Alternatively, you can install via <a href="https://hacs.xyz/">HACS</a>.
</p>

<p align="center">
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=SupaHotMoj0&repository=tuya_ble&category=integration">
    <img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="HACS">
  </a>
</p>

<h2 align="center">Usage</h2>

<p align="center">
  After adding to Home Assistant, the integration should automatically discover all supported Bluetooth devices, or you can add discoverable devices manually.
</p>

<p align="center">
  Please note that while the integration operates locally, connecting to a Tuya BLE device requires a device ID and encryption key from the Tuya IoT cloud. These credentials can be obtained using the same credentials as the official Tuya integration. For more information on obtaining these credentials, please refer to the official <a href="https://www.home-assistant.io/integrations/tuya/">Tuya integration documentation</a>.
</p>

<h2 align="center">Supported Devices List</h2>

  <ul>
    <li>
      <details>
        <summary><h3>Fingerbots (Category ID: 'szjqr')</h3></summary>
        <ul>
          <li>Fingerbot (Product IDs: 'ltak7e1p', 'y6kttvd6', 'yrnk7mnn', 'nvr2rocq', 'bnt7wajf', 'rvdceqjh', '5xhbk964'): The original device, powered by a CR2 battery.</li>
          <li>Adaprox Fingerbot (Product ID: 'y6kttvd6'): Features a built-in battery with USB type C charging.</li>
          <li>Fingerbot Plus (Product IDs: 'blliqpsj', 'ndvkgsrm', 'yiihr7zh', 'neq16kgd'): Almost the same as the original, with a sensor button for manual control.</li>
          <li>CubeTouch 1s (Product ID: '3yqdo5yt'): Features a built-in battery with USB type C charging.</li>
          <li>CubeTouch II (Product ID: 'xhf790if'): Features a built-in battery with USB type C charging.</li>
        </ul>
        <p>All features are available in Home Assistant. Programming (series of actions) is implemented for the Fingerbot Plus. Exposed entities include 'Program' (switch), 'Repeat forever', 'Repeats count', 'Idle position', and 'Program' (text). The format of the program text is: 'position[/time];...' where the position is in percentages and optional time is in seconds (zero if missing).</p>
      </details>
    </li>
    <li>
      <details>
        <summary><h3>Temperature and Humidity Sensors (Category ID: 'wsdcg')</h3></summary>
        <ul>
          <li>Soil Moisture Sensor (Product ID: 'ojzlzzsw').</li>
        </ul>
      </details>
    </li>
    <li>
      <details>
        <summary><h3>CO2 Sensors (Category ID: 'co2bj')</h3></summary>
        <ul>
          <li>CO2 Detector (Product ID: '59s19z5m').</li>
        </ul>
      </details>
    </li>
    <li>
      <details>
        <summary><h3>Smart Locks (Category ID: 'ms')</h3></summary>
        <ul>
          <li>Smart Lock (Product IDs: 'ludzroix', 'isk2p555').</li>
        </ul>
      </details>
    </li>
    <li>
      <details>
        <summary><h3>Climate (Category ID: 'wk')</h3></summary>
        <ul>
          <li>Thermostatic Radiator Valve (Product IDs: 'drlajpqc', 'nhj2j7su').</li>
        </ul>
      </details>
    </li>
    <li>
      <details>
        <summary><h3>Smart Water Bottle (Category ID: 'znhsb')</h3></summary>
        <ul>
          <li>Smart Water Bottle (Product ID: 'cdlandip').</li>
        </ul>
      </details>
    </li>
    <li>
      <details>
        <summary><h3>Irrigation Computer (Category ID: 'ggq')</h3></summary>
        <ul>
          <li>Irrigation Computer (Product ID: '6pahkcau').</li>
        </ul>
      </details>
    </li>
  </ul>
</details>
