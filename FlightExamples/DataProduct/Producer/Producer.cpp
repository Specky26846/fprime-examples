// ======================================================================
// \title  Producer.cpp
// \author mstarch
// \brief  cpp file for Producer component implementation class
// ======================================================================

#include "../../DataProduct/Producer/Producer.hpp"
#include <cmath>

namespace DataProduct {

// ----------------------------------------------------------------------
// Component construction and destruction
// ----------------------------------------------------------------------

Producer ::Producer(const char* const compName)
    : ProducerComponentBase(compName), m_count(0), m_container(), m_containerValid(false) {}

Producer ::~Producer() {}

// ----------------------------------------------------------------------
// Handler implementations for typed input ports
// ----------------------------------------------------------------------

void Producer ::run_handler(FwIndexType portNum, U32 context) {
    if (not this->m_containerValid) {
        // Record count * size of each record * 2 record types
        const FwSizeType containerSize = RECORD_COUNT * (SinusoidRecordType::SERIALIZED_SIZE + sizeof(FwDpIdType)) * 2;

        // Initialize the data product container
        Fw::Success status = this->dpGet_SinusoidContainer(containerSize, this->m_container);
        if (status != Fw::Success::SUCCESS) {
            this->log_WARNING_HI_DpMemoryFailure(containerSize);
        } else {
            this->m_containerValid = true;
            this->m_container.setTimeTag(this->getTime());
            this->log_WARNING_HI_DpMemoryFailure_ThrottleClear();
        }
    }
    // If we have a valid container, serialize records into it
    if (this->m_containerValid) {
        Fw::Time currentFwTime = this->getTime();
        Fw::TimeValue currentTime = Fw::TimeValue(currentFwTime.getTimeBase(), currentFwTime.getContext(),
                                                  currentFwTime.getSeconds(), currentFwTime.getUSeconds());
        F64 time = static_cast<F64>(currentTime.get_seconds()) + static_cast<F64>(currentTime.get_useconds()) / 1.0e6;
        // Calculate sine and cosine records
        SinusoidRecordType sineRecord, cosineRecord;
        sineRecord.set_timeTag(currentTime);
        sineRecord.set_value(std::sin(time));
        cosineRecord.set_timeTag(currentTime);
        cosineRecord.set_value(std::cos(time));

        // Serialize the records into the data product container
        Fw::SerializeStatus status = this->m_container.serializeRecord_SineRecord(sineRecord);
        FW_ASSERT(status == Fw::SerializeStatus::FW_SERIALIZE_OK);
        status = this->m_container.serializeRecord_CosineRecord(cosineRecord);
        FW_ASSERT(status == Fw::SerializeStatus::FW_SERIALIZE_OK);
        this->m_count += 1;

        // If we've reached the record count, send the full product
        if (this->m_count == RECORD_COUNT) {
            this->dpSend(this->m_container);
            this->m_count = 0;
            this->m_containerValid = false;
        }
    }
}

// ----------------------------------------------------------------------
// Handler implementations for commands
// ----------------------------------------------------------------------

void Producer ::Dp_cmdHandler(FwOpcodeType opCode,
                            U32 cmdSeq,
                            const DataProduct::Producer_DpReqType& reqType,
                            U32 priority,
                            const Fw::DpCfg::ProcType& proc) {

    // Calculate the size needed for the container
    const FwSizeType containerSize = RECORD_COUNT * (SinusoidRecordType::SERIALIZED_SIZE + sizeof(FwDpIdType)) * 2;

    // Allocate the data product container
    DpContainer container;
    Fw::Success status = this->dpGet_SinusoidContainer(containerSize, container);

    if (status != Fw::Success::SUCCESS) {
        // Memory allocation failed
        this->log_WARNING_HI_DpMemoryFailure(containerSize);
        this->cmdResponse_out(opCode, cmdSeq, Fw::CmdResponse::EXECUTION_ERROR);
        return;
    }

    // Set the timestamp
    container.setTimeTag(this->getTime());

    // Set the priority from command parameter
    container.setPriority(priority);

    // Set the processing type (compression) from command parameter
    container.setProcTypes(proc);

    // Log that we're starting
    this->log_ACTIVITY_LO_DpStarted(RECORD_COUNT);

    // Generate and serialize records into the container
    Fw::Time currentFwTime = this->getTime();
    Fw::TimeValue currentTime = Fw::TimeValue(currentFwTime.getTimeBase(), currentFwTime.getContext(),
                                                currentFwTime.getSeconds(), currentFwTime.getUSeconds());
    F64 time = static_cast<F64>(currentTime.get_seconds()) + static_cast<F64>(currentTime.get_useconds()) / 1.0e6;

    // Serialize RECORD_COUNT pairs of sine/cosine records
    for (FwSizeType i = 0; i < RECORD_COUNT; i++) {
        SinusoidRecordType sineRecord, cosineRecord;
        sineRecord.set_timeTag(currentTime);
        sineRecord.set_value(std::sin(time + i * 0.01));
        cosineRecord.set_timeTag(currentTime);
        cosineRecord.set_value(std::cos(time + i * 0.01));
        
        Fw::SerializeStatus serStatus = container.serializeRecord_SineRecord(sineRecord);
        FW_ASSERT(serStatus == Fw::SerializeStatus::FW_SERIALIZE_OK);
        serStatus = container.serializeRecord_CosineRecord(cosineRecord);
        FW_ASSERT(serStatus == Fw::SerializeStatus::FW_SERIALIZE_OK);
    }

    // Send the data product
    this->dpSend(container);

    // Log completion
    this->log_ACTIVITY_LO_DpComplete(RECORD_COUNT);

    // Send command success response
    this->cmdResponse_out(opCode, cmdSeq, Fw::CmdResponse::OK);

}


}  // namespace DataProduct
