_start:
    # 0x2000_0000 -> DMEM base
    # s11 will += 4 for every debug item
    lui     s11, 0x20000

    # s2 = 51 = 0b0011_0011
    addi    s2, zero, 51
    # s3 = 5 = 0b0000_0101
    addi    s3, zero, 5

    # s1 = 1
    addi    s1, zero, 1
    # s4 = 7
    addi    s4, zero, 7
    # s5 = -7
    addi    s5, zero, -7

    # s6 = 0xCCCCEEFF
    # Equivalent to: li s6, 0xCCCCEEFF
    lui     s6, 0xCCCCF
    addi    s6, s6, -257

    # 8 instructions above
    # offset = 32

    # >> auipc
    # 32 = offset + 0
    auipc   t0, 0
    sw      t0, 0(s11)
    addi    s11, s11, 4

    # >> jalr
    # 48 = offset + 16
    jalr    t0, t0, 20
    addi    t0, zero, 0
    sw      t0, 0(s11)
    addi    s11, s11, 4

    # >> jal
    # 64 = offset + 32
    jal     t0, _label_jal
    addi    t0, zero, 0
_label_jal:
    sw      t0, 0(s11)
    addi    s11, s11, 4

    # >> sw
    # 0xCCCCEEFF = -858984705
    sw      s6, 0(s11)
    addi    s10, s11, 0
    addi    s11, s11, 4

    # >> sb
    # 0x0000FF00 = 65280
    sb      zero, 3(s11)
    sb      zero, 2(s11)
    sb      zero, 0(s11)
    sb      s6, 1(s11)
    addi    s11, s11, 4

    # >> lw
    # 0xCCCCEEFF = -858984705
    lw      t0, 0(s10)
    sw      t0, 0(s11)
    addi    s11, s11, 4

    # >> lb
    # 0xFFFFFFFF = -1
    lb      t0, 0(s10)
    sw      t0, 0(s11)
    addi    s11, s11, 4

    # >> add
    # 51 + 5 = 56
    add     t0, s2, s3
    sw      t0, 0(s11)
    addi    s11, s11, 4

    # >> sub
    # 51 - 5 = 46
    sub     t0, s2, s3
    sw      t0, 0(s11)
    addi    s11, s11, 4

    # >> and
    # 51 & 5 = 1
    and     t0, s2, s3
    sw      t0, 0(s11)
    addi    s11, s11, 4

    # >> slt
    # 1 < 7 = 1
    slt     t0, s1, s4
    sw      t0, 0(s11)
    addi    s11, s11, 4

    # >> addi
    # 51 - 10 = 41
    addi    t0, s2, -10
    sw      t0, 0(s11)
    addi    s11, s11, 4

    # >> andi
    # 5 & 3 = 1
    andi    t0, s3, 3
    sw      t0, 0(s11)
    addi    s11, s11, 4

    # >> slti
    # 1 < 0 = 0
    slti    t0, s1, 0
    sw      t0, 0(s11)
    addi    s11, s11, 4

    # >> beq
    # (-7 == 7) = 0
    addi    t0, zero, 1
    beq     s5, s4, _label_beq
    addi    t0, zero, 0
_label_beq:
    sw      t0, 0(s11)
    addi    s11, s11, 4

    # >> blt
    # (-7 < 7) = 1
    addi    t0, zero, 1
    blt     s5, s4, _label_blt
    addi    t0, zero, 0
_label_blt:
    sw      t0, 0(s11)
    addi    s11, s11, 4

    addi    zero, zero, 0
    addi    zero, zero, 0

    .word 0x00100073
