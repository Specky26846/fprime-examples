module DataProduct {
    @ Record structure for sinusoidal data storing the timestamp and value
    struct SinusoidRecordType {
        timeTag: Fw.TimeValue
        value: F32
    }

    @ A data product producer
    passive component Producer {
        @ Schedule input port
        sync input port run: Svc.Sched

        @ Command for generating a DP
        sync command Dp(reqType: DpReqType, $priority: U32, proc: Fw.DpCfg.ProcType)

        enum DpReqType {
            IMMEDIATE
            ASYNC
        }

        @ Data product record for sine wave
        product record SineRecord: SinusoidRecordType id 0

        @ Data product record for cosine wave
        product record CosineRecord: SinusoidRecordType id 1

        @ Data product container containing samples from both waves
        product container SinusoidContainer id 0 default priority 10

        @ Event indicating failure to allocate memory for data product
        event DpMemoryFailure(allocationSize: FwSizeType) \
            severity warning high id 0 \
            format "Memory allocation of size {} for data product container failed" \
            throttle 2

        ###############################################################################
        # Standard AC Ports: Required for Channels, Events, Commands, and Parameters  #
        ###############################################################################
        @ Port for requesting the current time
        time get port timeCaller

        @ Data product get port: allocates a data product container
        product get port productGetOut

        @ Data product send port: sends the filled data product container
        product send port productSendOut

        @ For sending events
        import Fw.Event

        @ DP started event
        event DpStarted(records: U32) severity activity low id 1 format "Writing {} DP records"

        @ DP complete event  
        event DpComplete(records: U32) severity activity low id 2 format "Finished writing {} DP records"

        @ Port for sending command registrations
        command reg port cmdRegOut

        @ Port for receiving commands
        command recv port cmdIn

        @ Port for sending command responses
        command resp port cmdResponseOut

    }
}