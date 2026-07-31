module ManagerWorkerSubtopologyConfig {
    # Base ID for your subtopology. All instantiated components will be offsets of this
    # Following ExamplesDeployment convention: 0xDSSCCxxx where D=1, SS=01 for ManagerWorker subtopology
    constant ManagerWorkerSubtopology_BASE_ID = 0x10100000
    
    # include default Queue and Stack sizes here
    module Defaults {
        constant QUEUE_SIZE = 10
        constant STACK_SIZE = 64 * 1024
    }

    module Priorities {
         constant manager = 90
         constant worker = 30
    }
}
