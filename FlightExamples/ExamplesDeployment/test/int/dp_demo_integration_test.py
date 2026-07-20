import json
from pathlib import Path

from fprime_gds.common.dp.decoder import DataProductDecoder


def test_dp_send(fprime_test_api):
    """Test that DPs are generated and received on the ground"""

    # Run Dp command to send a data product
    fprime_test_api.send_and_assert_command(
        "ExamplesDeployment.dpProducer.Dp", ["IMMEDIATE", 1, "PROC_TYPE_NONE"]
    )
    # Wait for DpStarted event
    result = fprime_test_api.await_event("ExamplesDeployment.dpProducer.DpStarted", start=0, timeout=5)
    assert result
    # Wait for DpComplete event
    result = fprime_test_api.await_event("ExamplesDeployment.dpProducer.DpComplete", start=0, timeout=10)
    assert result
    # Check for FileWritten event and capture the name of the file that was created
    file_result = fprime_test_api.await_event(
        "DataProducts.dpWriter.FileWritten", start=0, timeout=10
    )
    dp_file_path = file_result.get_display_text().split().pop()
    # Verify that the file exists. The FSW writes ./DpCat relative to its
    # working directory, so the test must run from that same directory.
    assert Path(dp_file_path).is_file()


def test_dp_decode(fprime_test_api):
    """Test decoding DPs via DataProductDecoder with PROC_TYPE_LOSSLESS - compressed"""

    # Run Dp command to send a data product WITH LOSSLESS COMPRESSION
    fprime_test_api.send_and_assert_command(
        "ExamplesDeployment.dpProducer.Dp", ["IMMEDIATE", 1, "PROC_TYPE_LOSSLESS"]
    )
    # Check for FileWritten event and capture the name of the file that was created
    file_result = fprime_test_api.await_event(
        "DataProducts.dpWriter.FileWritten", start=0, timeout=10
    )
    dp_file_path = file_result.get_display_text().split().pop()
    # Verify that the file exists. The FSW writes ./DpCat relative to its
    # working directory, so the test must run from that same directory.
    assert Path(dp_file_path).is_file(), "Dp file not downlinked correctly"

    # Decode DP file - KEY TEST FOR COMPRESSION/DECOMPRESSION
    # If decompression doesn't work, this will fail
    decoded_file_name = Path(dp_file_path).name.replace(".fdp", ".json")
    DataProductDecoder(
        fprime_test_api.dictionaries, dp_file_path, decoded_file_name
    ).process()
    assert Path(decoded_file_name).is_file(), "Decoded file not created"

    # Open both reference JSON and output JSON and compare
    with open(Path(__file__).parent / "dp_ref_output.json", "r") as ref_file, open(
        decoded_file_name, "r"
    ) as output_file:
        ref_json = json.load(ref_file)
        output_json = json.load(output_file)

        # Verify that ProcTypes indicates compression was used
        assert output_json["Header"]["ProcTypes"]["value"] == 1, \
            f"Expected ProcTypes=1 (lossless), got {output_json['Header']['ProcTypes']['value']}"

        # Exclude Time and Checksum header fields since the timestamp will change every time
        ref_json["Header"].pop("Time")
        output_json["Header"].pop("Time")
        ref_json["Header"].pop("Checksum")
        output_json["Header"].pop("Checksum")
        # Exclude ProcTypes since ref uses NONE (0) but this test uses LOSSLESS (1)
        ref_json["Header"].pop("ProcTypes")
        output_json["Header"].pop("ProcTypes")

        # Every other field in Header and Data should be exactly the same
        # This proves decompression correctly recovered the original data
        assert ref_json == output_json, "Decompressed data does not match reference"


def test_dp_decode_proc_type_none(fprime_test_api):
    """Test decoding DPs with PROC_TYPE_NONE - baseline/uncompressed"""

    fprime_test_api.send_and_assert_command(
        "ExamplesDeployment.dpProducer.Dp", ["IMMEDIATE", 1, "PROC_TYPE_NONE"]
    )
    file_result = fprime_test_api.await_event(
        "DataProducts.dpWriter.FileWritten", start=0, timeout=10
    )
    dp_file_path = file_result.get_display_text().split().pop()
    assert Path(dp_file_path).is_file(), "DP file not found"

    # Decode and verify
    decoded_file_name = Path(dp_file_path).name.replace(".fdp", "_none.json")
    DataProductDecoder(
        fprime_test_api.dictionaries, dp_file_path, decoded_file_name
    ).process()
    assert Path(decoded_file_name).is_file(), "Decoded file not created"

    with open(decoded_file_name, "r") as output_file:
        output_json = json.load(output_file)
        # Verify ProcTypes is NONE (0)
        assert output_json["Header"]["ProcTypes"]["value"] == 0, \
            f"Expected ProcTypes=0 (none), got {output_json['Header']['ProcTypes']['value']}"


def test_dp_decode_proc_type_lossy(fprime_test_api):
    """Test decoding DPs with PROC_TYPE_LOSSY - verifies lossy compression/decompression works"""

    fprime_test_api.send_and_assert_command(
        "ExamplesDeployment.dpProducer.Dp", ["IMMEDIATE", 1, "PROC_TYPE_LOSSY"]
    )
    file_result = fprime_test_api.await_event(
        "DataProducts.dpWriter.FileWritten", start=0, timeout=10
    )
    dp_file_path = file_result.get_display_text().split().pop()
    assert Path(dp_file_path).is_file(), "Lossy compressed DP file not found"

    # Decode the lossy compressed DP - KEY TEST for lossy compression/decompression
    decoded_file_name = Path(dp_file_path).name.replace(".fdp", "_lossy.json")
    DataProductDecoder(
        fprime_test_api.dictionaries, dp_file_path, decoded_file_name
    ).process()
    assert Path(decoded_file_name).is_file(), "Failed to decode lossy compressed DP"

    with open(decoded_file_name, "r") as output_file:
        output_json = json.load(output_file)

        # Verify that ProcTypes indicates lossy compression was used
        assert output_json["Header"]["ProcTypes"]["value"] == 2, \
            f"Expected ProcTypes=2 (lossy), got {output_json['Header']['ProcTypes']['value']}"

        # Verify basic structure is intact (lossy may have data loss, so no exact comparison)
        assert "Header" in output_json, "Missing Header in decoded lossy DP"
        assert "Records" in output_json, "Missing Records in decoded lossy DP"
        assert len(output_json["Records"]) > 0, "No records in decoded lossy DP"