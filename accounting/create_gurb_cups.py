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

        gurb_id = self.c.SomGurb.search([("code", "=", self.gurb_code)])
        if not gurb_id:
            print("No s'ha trobat cap GURB amb codi {}.".format(self.gurb_code))
            return
        else:
            gurb_id = gurb_id[0]

        for contract in self.contract_list:
            pol_br = self.c.GiscedataPolissa.browse(
                [("name", "=", contract["name"])]
            )
            if not pol_br:
                print("No s'ha trobat la pòlissa {}.".format(contract["name"]))
                continue

            gurb_cups_id = self.c.SomGurbCups.search([
                ("gurb_id", "=", gurb_id),
                ("cups_id", "=", pol_br[0].cups.id),
            ])
            if gurb_cups_id:
                print(
                    "El CUPS {} ja és al GURB {}.".format(
                        pol_br[0].cups.name,
                        self.gurb_code,
                    )
                )
                continue

            gurb_cups_id = self.c.SomGurbCups.create({
                "gurb_id": gurb_id,
                "cups_id": pol_br[0].cups.id,
                "start_date": str(date.today()),
            })
            if gurb_cups_id:
                self.c.SomGurbCupsBeta.create({
                    "active": True,
                    "gurb_cups_id": gurb_cups_id.id,
                    "beta_kw": contract["beta"],
                    "extra_beta_kw": 0.0,
                    "start_date": str(date.today()),
                })

                n_gurb_cups += 1

        print("S'han creat correctament {} GURB CUPS.".format(n_gurb_cups))


enrolment_file = sys.argv[1]
gurb_code = sys.argv[2]
contract_list = []

with open(enrolment_file, "r") as csvfile:
    reader = csv.reader(csvfile, delimiter=",")
    for row in reader:
        contract_list.append(
            {
                "name": row[0],
                "beta": float(row[1].replace(',', '.')),
            }
        )

cgc = CreateGurbCups(c, contract_list, gurb_code)
cgc.createGurbCups()
