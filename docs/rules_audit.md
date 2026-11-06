# Rules audit – sold bundles vs catalogue rules

The rules engine (`backend/app/services/rules_engine.py`) re-checked all **368** activated bundles in `smb_leads.csv`. **48** (13%) break at least one catalogue rule – evidence that manual quoting mis-sells and that the rules engine must be the source of truth.

Profile used per lead: segment, `employee_count`, `num_sites`, `city_tier`; GSTIN counts as present when `has_gstin == 'Y'`. Dependency = a product with `requires_one_of` sold without any of those products.

## Violations by type

| Rule | Violations |
|---|---|
| city tier | 24 |
| GSTIN | 12 |
| dependency | 9 |
| employees | 8 |

A bundle can break more than one rule, so the total exceeds the number of flagged bundles.

## Flagged bundles

| Lead | Business | City (tier) | Staff | Sites | GSTIN | Bundle | Violations |
|---|---|---|---|---|---|---|---|
| L00086 | Physiotherapy clinic | Bengaluru (1) | 3 | 1 | Y | `P03x1;P07x4;P16x3;P20x3;P17x1;P12x3;P11x1;P09x1;P14x1` | P03: Biz Fibre 1G needs at least 5 staff. |
| L00207 | Insurance agency | Kochi (2) | 21 | 1 | Y | `P03x1;P08x3;P16x14;P17x1;P12x2;P11x1;P14x1` | P03: Biz Fibre 1G is available only in tier-1 cities. |
| L00242 | Dental clinic | Surat (2) | 7 | 1 | Y | `P03x1;P07x1;P16x5;P20x7;P17x1` | P03: Biz Fibre 1G is available only in tier-1 cities. |
| L00355 | Insurance agency | Patna (2) | 12 | 1 | N | `P03x1;P07x1;P16x12;P20x8;P11x1` | P03: Biz Fibre 1G is available only in tier-1 cities and needs an active GSTIN. |
| L00674 | Law office | Jaipur (2) | 9 | 1 | Y | `P03x1;P08x2;P16x9;P11x1` | P03: Biz Fibre 1G is available only in tier-1 cities. |
| L00751 | Insurance agency | Indore (2) | 18 | 1 | Y | `P03x1;P07x3;P16x5;P12x3` | P03: Biz Fibre 1G is available only in tier-1 cities. |
| L00764 | Real estate agency | Bengaluru (1) | 14 | 2 | N | `P03x1;P08x2;P16x10;P12x4` | P03: Biz Fibre 1G needs an active GSTIN.; P12: Cloud Telephony / SIP needs an active GSTIN. |
| L00974 | Boutique | Bengaluru (1) | 6 | 1 | N | `P01x1;P07x2;P23x1;P15x1` | P15: WhatsApp Business API Starter needs an active GSTIN. |
| L00983 | Law office | Chennai (1) | 3 | 1 | Y | `P03x1;P08x3;P16x3;P20x3;P11x1` | P03: Biz Fibre 1G needs at least 5 staff. |
| L01045 | Travel agency | Chennai (1) | 3 | 2 | Y | `P03x1;P07x3;P16x3;P20x3;P17x1` | P03: Biz Fibre 1G needs at least 5 staff. |
| L01079 | Physiotherapy clinic | Chennai (1) | 4 | 1 | Y | `P03x1;P08x4;P16x4` | P03: Biz Fibre 1G needs at least 5 staff. |
| L01089 | Printing press | Indore (2) | 90 | 1 | Y | `P05x1;P08x2;P16x11;P23x6;P11x1` | P11: Static IP needs an internet connection in the same bundle. |
| L01104 | Plastic moulding unit | Surat (2) | 99 | 1 | Y | `P06x1;P08x3;P16x10;P24x12;P23x5;P20x10;P11x1` | P11: Static IP needs an internet connection in the same bundle. |
| L01138 | Physiotherapy clinic | Nashik (2) | 24 | 1 | Y | `P03x1;P07x1;P16x15;P11x1` | P03: Biz Fibre 1G is available only in tier-1 cities. |
| L01199 | Plastic moulding unit | Mumbai (1) | 13 | 2 | Y | `P06x1;P08x3;P16x10;P24x9;P20x4` | P06: Internet Leased Line 100 needs at least 25 staff. |
| L01464 | Dental clinic | Jaipur (2) | 24 | 1 | Y | `P03x1;P07x1;P16x5;P20x9;P11x1;P09x1` | P03: Biz Fibre 1G is available only in tier-1 cities. |
| L01511 | Packaging unit | Lucknow (2) | 32 | 1 | Y | `P05x1;P08x6;P16x12;P20x5;P11x1` | P11: Static IP needs an internet connection in the same bundle. |
| L01817 | Coaching centre | Lucknow (2) | 4 | 1 | Y | `P03x1;P07x3;P16x4;P12x2` | P03: Biz Fibre 1G is available only in tier-1 cities and needs at least 5 staff. |
| L01828 | Food processing unit | Coimbatore (2) | 110 | 1 | Y | `P03x1;P08x4;P16x6` | P03: Biz Fibre 1G is available only in tier-1 cities. |
| L01851 | Packaging unit | Nashik (2) | 119 | 2 | Y | `P03x1;P08x3;P16x8` | P03: Biz Fibre 1G is available only in tier-1 cities. |
| L02014 | Architecture studio | Visakhapatnam (2) | 4 | 1 | Y | `P03x1;P08x3;P16x4;P20x4;P17x1;P12x3;P14x1` | P03: Biz Fibre 1G is available only in tier-1 cities and needs at least 5 staff. |
| L02358 | Sweet shop | Kolkata (1) | 3 | 1 | N | `P01x1;P07x2;P19x1;P15x1` | P15: WhatsApp Business API Starter needs an active GSTIN. |
| L02588 | Auto-parts unit | Delhi (1) | 75 | 1 | Y | `P05x1;P08x3;P16x11;P20x12;P11x1` | P11: Static IP needs an internet connection in the same bundle. |
| L02859 | Printing press | Jaipur (2) | 13 | 1 | Y | `P03x1;P08x2;P16x13;P21x1;P23x4` | P03: Biz Fibre 1G is available only in tier-1 cities. |
| L02870 | Physiotherapy clinic | Visakhapatnam (2) | 16 | 1 | Y | `P03x1;P08x4;P16x11;P20x4` | P03: Biz Fibre 1G is available only in tier-1 cities. |
| L02943 | Food processing unit | Hyderabad (1) | 64 | 1 | Y | `P05x1;P08x5;P16x18;P21x1;P20x6;P11x1` | P11: Static IP needs an internet connection in the same bundle. |
| L03010 | Furniture workshop | Delhi (1) | 46 | 1 | Y | `P06x1;P08x5;P16x11;P20x6;P11x1;P25x6` | P11: Static IP needs an internet connection in the same bundle. |
| L03058 | Electronics retail chain | Mumbai (1) | 43 | 8 | N | `P02x8;P09x8;P08x6;P19x8;P10x8;P23x16;P22x8` | P10: Managed SD-WAN needs an active GSTIN. |
| L03221 | Bakery | Ahmedabad (1) | 3 | 1 | N | `P01x1;P07x1;P15x1` | P15: WhatsApp Business API Starter needs an active GSTIN. |
| L03292 | Diagnostic lab | Visakhapatnam (2) | 5 | 1 | N | `P01x1;P07x2;P16x5;P20x4;P14x1` | P14: Business SMS 10k needs an active GSTIN. |
| L03419 | Plastic moulding unit | Ahmedabad (1) | 62 | 1 | Y | `P05x1;P08x6;P16x9;P21x1;P24x10;P11x1` | P11: Static IP needs an internet connection in the same bundle. |
| L03473 | Law office | Vadodara (2) | 18 | 1 | Y | `P03x1;P08x4;P16x7;P12x4;P09x1` | P03: Biz Fibre 1G is available only in tier-1 cities. |
| L03516 | Law office | Coimbatore (2) | 22 | 1 | Y | `P03x1;P07x3;P16x4;P17x1;P11x1;P09x1` | P03: Biz Fibre 1G is available only in tier-1 cities. |
| L03673 | Travel agency | Patna (2) | 23 | 1 | Y | `P03x1;P08x2;P16x7;P20x4;P11x1;P14x1` | P03: Biz Fibre 1G is available only in tier-1 cities. |
| L03774 | Coaching centre | Patna (2) | 6 | 1 | N | `P03x1;P07x2;P16x6;P09x1` | P03: Biz Fibre 1G is available only in tier-1 cities and needs an active GSTIN. |
| L03842 | Sweet shop | Chennai (1) | 4 | 1 | N | `P01x1;P07x2;P22x1;P23x1;P15x1` | P15: WhatsApp Business API Starter needs an active GSTIN. |
| L03872 | Auto-parts unit | Kochi (2) | 33 | 1 | Y | `P03x1;P08x4;P16x14;P11x1` | P03: Biz Fibre 1G is available only in tier-1 cities. |
| L04070 | Stationery shop | Ludhiana (2) | 2 | 1 | N | `P01x1;P07x2;P19x1;P15x1;P18x1` | P15: WhatsApp Business API Starter needs an active GSTIN. |
| L04272 | Textile unit | Bhopal (2) | 25 | 1 | Y | `P03x1;P08x4;P16x19;P21x1;P23x3` | P03: Biz Fibre 1G is available only in tier-1 cities. |
| L04350 | Furniture workshop | Mumbai (1) | 147 | 2 | Y | `P06x1;P08x6;P16x11;P24x9;P11x1` | P11: Static IP needs an internet connection in the same bundle. |
| L04451 | Furniture workshop | Mysuru (2) | 53 | 2 | Y | `P03x1;P08x4;P16x6;P21x1;P11x1` | P03: Biz Fibre 1G is available only in tier-1 cities. |
| L04464 | Diagnostic lab | Kochi (2) | 15 | 1 | Y | `P03x1;P08x3;P16x15;P20x5;P17x1;P09x1` | P03: Biz Fibre 1G is available only in tier-1 cities. |
| L04566 | Textile unit | Kochi (2) | 39 | 1 | Y | `P03x1;P08x6;P16x5;P21x1;P24x12;P20x8;P25x3` | P03: Biz Fibre 1G is available only in tier-1 cities. |
| L04596 | Plastic moulding unit | Vadodara (2) | 147 | 1 | Y | `P03x1;P08x5;P16x6;P20x7` | P03: Biz Fibre 1G is available only in tier-1 cities. |
| L04888 | Law office | Delhi (1) | 23 | 1 | N | `P01x1;P07x4;P16x9;P20x8;P17x1;P12x3;P09x1` | P12: Cloud Telephony / SIP needs an active GSTIN. |
| L04911 | Law office | Kochi (2) | 20 | 1 | Y | `P03x1;P08x4;P16x7;P20x8;P12x2;P11x1` | P03: Biz Fibre 1G is available only in tier-1 cities. |
| L04948 | Coaching centre | Kolkata (1) | 4 | 1 | Y | `P03x1;P07x4;P16x4;P12x4` | P03: Biz Fibre 1G needs at least 5 staff. |
| L04991 | Auto-parts unit | Ludhiana (2) | 54 | 1 | Y | `P05x1;P08x2;P16x19;P11x1` | P11: Static IP needs an internet connection in the same bundle. |
