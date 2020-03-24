
def get_single_chassi_power(redfish_url):

    global plugin

    plugin.set_current_command("Power")

    chassi_id = redfish_url.rstrip("/").split("/")[-1]

    redfish_url = f"{redfish_url}/Power"

    power_data = plugin.rf.get_view(redfish_url)

    power_supplies = power_data.get("PowerSupplies")

    fujitsu_power_sensors = None
    if plugin.rf.vendor == "Fujitsu":
        fujitsu_power_sensors = grab(power_data, f"Oem.{plugin.rf.vendor_dict_key}.ChassisPowerSensors")

    default_text = ""
    ps_num = 0
    ps_absent = 0
    if power_supplies:
        for ps in power_supplies:

            ps_num += 1

            status_data = get_status_data(grab(ps,"Status"))

            health = status_data.get("Health")
            operatinal_status = status_data.get("State")
            part_number = ps.get("PartNumber")
            model = ps.get("Model") or part_number
            last_power_output = ps.get("LastPowerOutputWatts") or ps.get("PowerOutputWatts")
            capacity_in_watt = ps.get("PowerCapacityWatts")
            bay = None

            oem_data = grab(ps, f"Oem.{plugin.rf.vendor_dict_key}")

            if oem_data is not None:

                if plugin.rf.vendor == "HPE":
                    bay = grab(oem_data, "BayNumber")
                    ps_hp_status = grab(oem_data, "PowerSupplyStatus.State")
                    if ps_hp_status is not None and ps_hp_status == "Unknown":
                        health = "CRITICAL"

                elif plugin.rf.vendor == "Lenovo":
                    bay = grab(oem_data, "Location.Info")

                if last_power_output is None and grab(oem_data, "PowerOutputWatts") is not None:
                    last_power_output = grab(oem_data, "PowerOutputWatts")

            if bay is None:
                bay = ps_num

            if capacity_in_watt is None:
                capacity_in_watt = grab(ps, "InputRanges.0.OutputWattage")

            # special Fujitsu case
            if fujitsu_power_sensors is not None and last_power_output is None:
                for fujitsu_power_sensor in fujitsu_power_sensors:
                    if fujitsu_power_sensor.get("Designation") == ps.get("Name"):
                        last_power_output = fujitsu_power_sensor.get("CurrentPowerConsumptionW")

            ps_inventory = PowerSupply(
                id = grab(ps, "MemberId") or ps_num,
                name = ps.get("Name"),
                model = model,
                bay = bay,
                health_status = health,
                operation_status = operatinal_status,
                last_power_output = last_power_output,
                serial = ps.get("SerialNumber"),
                type = ps.get("PowerSupplyType"),
                capacity_in_watt = capacity_in_watt,
                firmware = ps.get("FirmwareVersion"),
                vendor = ps.get("Manufacturer"),
                input_voltage = ps.get("LineInputVoltage"),
                part_number = ps.get("SparePartNumber") or ps.get("PartNumber"),
                chassi_ids = chassi_id
            )

            if args.verbose:
                ps_inventory.source_data = ps

            plugin.inventory.add(ps_inventory)

            printed_status = health
            printed_model = ""

            if health is None:
                printed_status = operatinal_status
                if operatinal_status == "Absent":
                    health = "OK"
                    ps_absent += 1
                if operatinal_status == "Enabled":
                    health = "OK"

            if model is not None:
                printed_model = "(%s) " % model.strip()

            status_text = "Power supply {bay} {model}status is: {status}".format(
                bay=str(bay), model=printed_model, status=printed_status)

            plugin.add_output_data("CRITICAL" if health not in ["OK", "WARNING"] else health, status_text)

            if last_power_output is not None:
                plugin.add_perf_data(f"ps_{bay}", int(last_power_output))

        default_text = "All power supplies (%d) are in good condition" % ( ps_num - ps_absent )

    else:
        plugin.add_output_data("UNKNOWN", f"No power supply data returned for API URL '{redfish_url}'")

    # get PowerRedundancy status
    power_redundancies = power_data.get("PowerRedundancy")
    if power_redundancies is None:
        power_redundancies = power_data.get("Redundancy")

    if power_redundancies:
        pr_status_summary_text = ""
        pr_num = 0
        for power_redundancy in power_redundancies:

            pr_status = power_redundancy.get("Status")


            if pr_status is not None:
                status = pr_status.get("Health")
                state = pr_status.get("State")

                if status is not None:
                    pr_num += 1
                    status = status.upper()

                    status_text = f"Power redundancy {pr_num} status is: {state}"

                    pr_status_summary_text += f" {status_text}"

                    plugin.add_output_data("CRITICAL" if status not in ["OK", "WARNING"] else status, status_text)

        if len(pr_status_summary_text) != 0:
            default_text += f" and{pr_status_summary_text}"

    # get Voltages status
    voltages = power_data.get("Voltages")

    if voltages is not None:
        voltages_num = 0
        for voltage in voltages:

            voltage_status = voltage.get("Status")

            if voltage_status is not None:
                status = voltage_status.get("Health")
                state = voltage_status.get("State")
                reading = voltage.get("ReadingVolts")
                name = voltage.get("Name")

                if status is not None:
                    voltages_num += 1
                    status = status.upper()

                    status_text = f"Voltage {name} (status: {status}/{state}): {reading}V"

                    plugin.add_output_data("CRITICAL" if status not in ["OK", "WARNING"] else status, status_text)

                    if reading is not None and name is not None:
                        try:
                            plugin.add_perf_data(f"voltage_{name}", float(reading))
                        except Exception:
                            pass

        if voltages_num > 0:
            default_text += f" and {voltages_num} Voltages are OK"

    plugin.add_output_data("OK", default_text, summary = True)

    return
