import os
import argparse

MemSize = 1000  # memory size, in reality, the memory size should be 2^32, but for this lab, for the space resaon, we keep it as this large number, but the memory is still 32-bit addressable.

OPCODE2TYPE = {
    "0110011": "R",
    "0010011": "I",
    "1101111": "J",
    "1100011": "B",
    "0100011": "S",
    "0000011": "I",
    "1111111": "HALT",
}


class InsMem(object):
    def __init__(self, name, ioDir):
        self.id = name
        print(ioDir)

        with open(ioDir + "/imem.txt") as im:
            self.IMem = [data.replace("\n", "") for data in im.readlines()]

    def readInstr(self, ReadAddress: int) -> str:
        # read instruction memory
        # return 32 bit hex val

        return "".join(self.IMem[ReadAddress:ReadAddress + 4])


class DataMem(object):
    def __init__(self, name, ioDir):
        self.id = name
        self.ioDir = ioDir
        with open(ioDir + "/dmem.txt") as dm:
            self.DMem = [data.replace("\n", "") for data in dm.readlines()]

    def readInstr(self, ReadAddress):
        # read data memory
        # return 32 bit hex val
        pass

    def writeDataMem(self, Address, WriteData):
        # write data into byte addressable memory
        pass

    def outputDataMem(self):
        resPath = self.ioDir + "/" + self.id + "_DMEMResult.txt"
        with open(resPath, "w") as rp:
            rp.writelines([str(data) + "\n" for data in self.DMem])


class RegisterFile(object):
    def __init__(self, ioDir):
        self.outputFile = ioDir + "RFResult.txt"
        self.Registers = [0x0 for i in range(32)]

    def readRF(self, Reg_addr):
        # Fill in
        pass

    def writeRF(self, Reg_addr, Wrt_reg_data):
        # Fill in
        pass

    def outputRF(self, cycle):
        op = ["-" * 70 + "\n", "State of RF after executing cycle:" + str(cycle) + "\n"]
        op.extend([str(val) + "\n" for val in self.Registers])
        if (cycle == 0):
            perm = "w"
        else:
            perm = "a"
        with open(self.outputFile, perm) as file:
            file.writelines(op)


class State(object):
    def __init__(self):
        self.IF = {"nop": False, "PC": 0}
        self.ID = {"nop": False, "Instr": 0}
        self.EX = {"nop": False, "Read_data1": 0, "Read_data2": 0, "Imm": 0, "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0,
                   "is_I_type": False, "rd_mem": 0,
                   "wrt_mem": 0, "alu_op": 0, "wrt_enable": 0}
        self.MEM = {"nop": False, "ALUresult": 0, "Store_data": 0, "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0, "rd_mem": 0,
                    "wrt_mem": 0, "wrt_enable": 0}
        self.WB = {"nop": False, "Wrt_data": 0, "Rs": 0, "Rt": 0, "Wrt_reg_addr": 0, "wrt_enable": 0}


class Core(object):
    def __init__(self, ioDir, imem, dmem):
        self.myRF = RegisterFile(ioDir)
        self.cycle = 0
        self.halted = False
        self.ioDir = ioDir
        self.state = State()
        self.nextState = State()
        self.ext_imem = imem
        self.ext_dmem = dmem

    def exeBTypeIns(self, elements):
        op, rs1, rs2, imm = elements['op'], elements['rs1'], elements['rs2'], elements['imm']
        rs1, rs2 = self.myRF.readRF(rs1), self.myRF.readRF(rs2)
        if op == 'BEQ':
            self.nextState.IF['PC'] = self.State.IF['PC'] + signedBin2int(imm) if rs1 == rs2 \
                else self.State.IF['PC'] + 4
        elif op == 'BNE':
            self.nextState.IF['PC'] = self.State.IF['PC'] + signedBin2int(imm) if rs1 != rs2 \
                else self.State.IF['PC'] + 4

    def exeJTypeIns(self, elements):
        op, rd, imm = elements['op'], elements['rd'], elements['imm']
        if op == 'JAL':
            self.myRF.writeRF(rd, self.State.IF['PC'] + 4)
            self.nextState.IF['PC'] = self.State.IF['PC'] + signedBin2int(imm)


    def exeITypeIns(self, elements):
        op, imm, rs1, rd = elements['op'], elements['imm'], elements['rs1'], elements['rd']
        rs1 = self.myRF.readRF(rs1)
        if op == 'ADDI':
            rd_value = rs1 + signedBin2int(imm)
        elif op == 'XORI':
            rd_value = rs1 ^ signedBin2int(imm)


    def exeRTypeIns(self, elements):
        funct7, funct3 = elements['funct7'], elements['funct3']
        pass




class SingleStageCore(Core):
    def __init__(self, ioDir, imem, dmem):
        super(SingleStageCore, self).__init__(ioDir + "/SS_", imem, dmem)
        self.opFilePath = ioDir + "/StateResult_SS.txt"

    def step(self):
        # Your implementation
        instruction = self.ext_imem.readInstr(self.state.IF["PC"])
        print(f"PC = {self.state.IF['PC']} ins = {instruction}")
        insType = getTypeByOpCode(instruction[-7:])
        print(insType)

        # parse and implement instruction
        if insType == "HALT":
            self.halted = True
            return
        elif insType == 'B':
            ins_elements = parseBTypeIns(instruction)
            self.exeBTypeIns(ins_elements)
        elif insType == 'J':
            ins_elements = parseJTypeIns(instruction)
            self.exeJTypeIns(ins_elements)
        else:
            # implement other types of instructions that won't affect nextState.IF["PC"]
            if insType == "R":
                ins_elements = parseRTypeIns(instruction)
            elif insType == "I":
                ins_elements = parseITypeIns(instruction)
            elif insType == "S":
                ins_elements = parseSTypeIns(instruction)
            self.nextState.IF["PC"] += 4

        # self.halted = True
        if self.state.IF["nop"]:
            self.halted = True

        self.myRF.outputRF(self.cycle)  # dump RF
        self.printState(self.nextState, self.cycle)  # print states after executing cycle 0, cycle 1, cycle 2 ...

        self.state = self.nextState  # The end of the cycle and updates the current state with the values calculated in this cycle
        self.cycle += 1

    def printState(self, state, cycle):
        printstate = ["-" * 70 + "\n", "State after executing cycle: " + str(cycle) + "\n"]
        printstate.append("IF.PC: " + str(state.IF["PC"]) + "\n")
        printstate.append("IF.nop: " + str(state.IF["nop"]) + "\n")

        if (cycle == 0):
            perm = "w"
        else:
            perm = "a"
        with open(self.opFilePath, perm) as wf:
            wf.writelines(printstate)


def parseRTypeIns(instruction: str) -> dict:
    funct7 = instruction[0:7]
    funct3 = instruction[17:20]
    op = ""
    if funct7 == "0100000":
        op = "SUB"
    else:
        if funct3 == "000":
            op = "ADD"
        elif funct3 == "100":
            op = "XOR"
        elif funct3 == "110":
            op = "OR"
        elif funct3 == "111":
            op = "AND"
    result = {
        "funct7": instruction[0:7],
        "rs2": instruction[7:12],
        "rs1": instruction[12:17],
        "funct3": instruction[17:20],
        "rd": instruction[20:25],
        "opcode": instruction[25:32],
        "op": op,
    }
    return result


def parseITypeIns(instruction: str) -> dict:
    funct3 = instruction[17:20]
    op = ""
    if funct3 == "000":
        op = "ADDI"
    elif funct3 == "100":
        op = "XORI"
    elif funct3 == "110":
        op = "ORI"
    elif funct3 == "111":
        op = "ANDI"

    result = {
        "imm": instruction[0:12],
        "rs1": instruction[12:17],
        "funct3": instruction[17:20],
        "rd": instruction[20:25],
        "opcode": instruction[25:32],
        "op": op,
    }
    return result


def parseSTypeIns(instruction: str) -> dict:
    result = {
        "imm": instruction[0:7] + instruction[20:25],
        "rs2": instruction[7:12],
        "rs1": instruction[12:17],
        "funct3": instruction[17:20],
        "opcode": instruction[25:32],
        "op": "SW"
    }
    return result


class FiveStageCore(Core):
    def __init__(self, ioDir, imem, dmem):
        super(FiveStageCore, self).__init__(ioDir + "FS_", imem, dmem)
        self.opFilePath = ioDir + "StateResult_FS.txt"

    def step(self):
        # Your implementation
        # --------------------- WB stage ---------------------

        # --------------------- MEM stage --------------------

        # --------------------- EX stage ---------------------

        # --------------------- ID stage ---------------------

        # --------------------- IF stage ---------------------

        self.halted = True
        if self.state.IF["nop"] and self.state.ID["nop"] and self.state.EX["nop"] and self.state.MEM["nop"] and \
                self.state.WB["nop"]:
            self.halted = True

        self.myRF.outputRF(self.cycle)  # dump RF
        self.printState(self.nextState, self.cycle)  # print states after executing cycle 0, cycle 1, cycle 2 ...

        self.state = self.nextState  # The end of the cycle and updates the current state with the values calculated in this cycle
        self.cycle += 1

    def printState(self, state, cycle):
        printstate = ["-" * 70 + "\n", "State after executing cycle: " + str(cycle) + "\n"]
        printstate.extend(["IF." + key + ": " + str(val) + "\n" for key, val in state.IF.items()])
        printstate.extend(["ID." + key + ": " + str(val) + "\n" for key, val in state.ID.items()])
        printstate.extend(["EX." + key + ": " + str(val) + "\n" for key, val in state.EX.items()])
        printstate.extend(["MEM." + key + ": " + str(val) + "\n" for key, val in state.MEM.items()])
        printstate.extend(["WB." + key + ": " + str(val) + "\n" for key, val in state.WB.items()])

        if (cycle == 0):
            perm = "w"
        else:
            perm = "a"
        with open(self.opFilePath, perm) as wf:
            wf.writelines(printstate)


def getTypeByOpCode(code: str) -> str:
    return OPCODE2TYPE[code]


def parseBTypeIns(ins):
    funct3 = ins[-15:-12]
    if funct3 == '000':
        op = 'BEQ'
    elif funct3 == '001':
        op = 'BNE'
    return {
        'op': op,
        'rs2': ins[-25:-20],
        'rs1': ins[-20:-15],
        'imm': ins[-32] + ins[-8] + ins[-31:-25] + ins[-12:-8]
    }


# def parseUTypeIns(ins):
#     return {
#         'imm': ins[-32:-12],
#         'rd': ins[-12:-7],
#         'opcode': ins[-7:]
#     }

def parseJTypeIns(ins):
    return {
        'op': 'JAL',
        'imm': ins[-32] + ins[-20:-12] + ins[-21] + ins[-31:-21],
        'rd': ins[-12:-7],
    }


def int2signedBin(d: int) -> str:
    '''
    :param n: a decimal number
    :return: a string represents the signed binary of d
    '''
    pass


def signedBin2int(b: str) -> int:
    '''
    :param b: a string represents a signed binary
    :return: the decimal number of b
    '''
    sign = b[0]     # the sign bit
    value = b[1:]
    if sign == '0':   # non-negative
        return int(value, 2)
    elif sign == '1':   # negative
        complement = ['1'  if bit == '0' else '0' for bit in value]
        i = -1
        while complement[i] == '1':
            complement[i] = '0'
            i -= 1
        complement[i] = '1'
        return -int(''.join(complement), 2)

if __name__ == "__main__":

    # parse arguments for input file location
    parser = argparse.ArgumentParser(description='RV32I processor')
    parser.add_argument('--iodir', default="", type=str, help='Directory containing the input files.')
    args = parser.parse_args()

    ioDir = os.path.abspath(args.iodir)
    print("IO Directory:", ioDir)

    imem = InsMem("Imem", ioDir)
    dmem_ss = DataMem("SS", ioDir)
    dmem_fs = DataMem("FS", ioDir)

    ssCore = SingleStageCore(ioDir, imem, dmem_ss)
    fsCore = FiveStageCore(ioDir, imem, dmem_fs)

    while (True):
        if not ssCore.halted:
            ssCore.step()

        if not fsCore.halted:
            fsCore.step()

        if ssCore.halted and fsCore.halted:
            break

    # dump SS and FS data mem.
    dmem_ss.outputDataMem()
    dmem_fs.outputDataMem()
