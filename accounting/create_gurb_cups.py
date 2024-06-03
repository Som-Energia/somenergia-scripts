#!/usr/bin/env python
# -*- coding: utf-8 -*-
import csv
import sys
from erppeek import Client
import configdb
from datetime import date

c = Client(**configdb.erppeek_test)


class CreateGurbCups:
    def __init__(self, c, contract_list, gurb_code):
        self.c = c
        self.contract_list = contract_list
        self.gurb_code = gurb_code

    def createGurbCups(self):
        n_gurb_cups = 0
        gurb_id = self.c.SomGurb.search([("code", "=", gurb_code)])
        if not gurb_id:
            print("No s'ha trobat cap GURB amb codi {} .".format(gurb_code))
            return
        for contract in self.contract_list:
            pol_br = self.c.GiscedataPolissa.browse(
                [("name", "=", contract["name"])]
            )
            if not pol_br:
                print("No s'ha trobat la pòlissa {}.".format(contract["name"]))
            gurb_cups_id = self.c.SomGurbCups().create({
                "gurb_id": gurb_id,
                "cups_id": pol_br.cups.id,
                "start_date": date.today(),
                "betas_ids": [
                    (0, 0, {
                        "beta_kw": contract["beta"],
                        "start_date": date.today(),
                    }),
                ],
            })
            if gurb_cups_id:
                n_gurb_cups += 1
        print("S'han creat correctament {} GURB CUPS.".format(n_gurb_cups))


enrolment_file = sys.argv[1]
gurb_code = sys.argv[2]
contract_list = []

with open(enrolment_file, "r") as csvfile:
    reader = csv.reader(csvfile, delimiter=",")
    next(reader)
    for row in reader:
        if row[0] and not row[1]:
            contract_list.append(
                {
                    "name": row[0],
                    "beta": row[1],
                }
            )

cgc = CreateGurbCups(c, contract_list, gurb_code)
cgc.createGurbCups()
