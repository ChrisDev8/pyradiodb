from zeep import Client, Settings, xsd
from dataclasses import dataclass, replace
from enum import StrEnum, IntEnum
from xml.dom.minidom import parseString
from tqdm import tqdm

import xml.etree.ElementTree as ET # noqa
import json
import math
import os

class Tag(StrEnum):
    UNKNOWN = "Unknown"
    DISPATCH = "Dispatch"
    TACTICAL = "Tactical"
    TALK = "Talk"
    EMERGENCY = "Emergency"
    RESCUE = "Rescue"
    HOSPITAL = "Hospital"
    INTEROP = "Interop"

    POLICE = "Police"
    POLICE_DISPATCH = "Police Dispatch"
    POLICE_TACTICAL = "Police Tactical"
    POLICE_TALK = "Police Talk"

    FIRE = "Fire"
    FIRE_DISPATCH = "Fire Dispatch"
    FIRE_TACTICAL = "Fire Tactical"
    FIRE_TALK = "Fire Talk"

    EMS = "EMS"
    EMS_DISPATCH = "EMS Dispatch"
    EMS_TACTICAL = "EMS Tactical"
    EMS_TALK = "EMS Talk"

    MILITARY = "Military"
    AIRCRAFT = "Aircraft"
    TRANSPORTATION = "Transportation"
    PUBLIC_WORKS = "Public Works"
    SCHOOLS = "Schools"
    BUSINESS = "Business"
    HAM_RADIO = "Ham Radio"
    FEDERAL = "Federal"
    RAILROAD = "Railroad"
    MEDIA = "Media"
    SECURITY = "Security"
    UTILITIES = "Utilities"
    DATA = "Data"
    CORRECTIONS = "Corrections"

    @classmethod
    def convert_tag(cls, tag: int):
        tag_table = {
            1: cls.DISPATCH,
            2: cls.POLICE_DISPATCH,
            3: cls.FIRE_DISPATCH,
            4: cls.EMS_DISPATCH,
            6: cls.TACTICAL,
            7: cls.POLICE_TACTICAL,
            8: cls.FIRE_TACTICAL,
            9: cls.EMS_TACTICAL,
            11: cls.INTEROP,
            12: cls.HOSPITAL,
            13: cls.HAM_RADIO,
            14: cls.PUBLIC_WORKS,
            15: cls.AIRCRAFT,
            16: cls.FEDERAL,
            17: cls.BUSINESS,
            20: cls.RAILROAD,
            21: cls.UNKNOWN,
            22: cls.TALK,
            23: cls.POLICE_TALK,
            24: cls.FIRE_TALK,
            25: cls.EMS_TALK,
            26: cls.TRANSPORTATION,
            29: cls.EMERGENCY,
            30: cls.MILITARY,
            31: cls.MEDIA,
            32: cls.SCHOOLS,
            33: cls.SECURITY,
            34: cls.UTILITIES,
            35: cls.DATA,
            36: cls.UNKNOWN,
            37: cls.CORRECTIONS
        }

        if tag in tag_table.keys():
            return tag_table[tag]
        else:
            return cls.UNKNOWN

    def serialize(self):
        return {
            "name": self.name,
            "value": self.value
        }

    @classmethod
    def deserialize(cls, tag: dict):
        return cls[tag["name"]]

class Modulation(IntEnum):
    UNKNOWN = 0
    P25 = 1
    P25_P1 = 2
    P25_P2 = 3
    DMR = 4
    NXDN = 5
    FM = 6
    AM = 7

    @classmethod
    def convert_stype(cls, s_type: int, s_flavor: int):
        system_map = {
            8: cls.P25,
            12: cls.DMR,
            11: cls.NXDN,
            7: cls.UNKNOWN,
            1: cls.UNKNOWN,
        }
        if s_type in system_map.keys():
            modulation = system_map[s_type]
            if modulation == cls.P25:
                if s_flavor == 20:
                    modulation = cls.P25_P1
                if s_flavor == 33:
                    modulation = cls.P25_P2
            return modulation
        else:
            return cls.UNKNOWN

    def serialize(self):
        return {
            "name": self.name,
            "value": self.value
        }

    @classmethod
    def deserialize(cls, tag: dict):
        return cls[tag["name"]]

class ToneType(IntEnum):
    NONE = 0
    CTCSS = 1
    DCS = 2

    def serialize(self):
        return {
            "name": self.name,
            "value": self.value
        }

    @classmethod
    def deserialize(cls, tag: dict):
        return cls[tag["name"]]

class Mode(IntEnum):
    UNKNOWN = 0
    FM = 1
    P25 = 2
    AM = 3
    FMN = 4
    TELEMETRY = 5
    DMR = 6
    NXDN48 = 7
    D_STAR = 8
    USB = 9
    LSB = 10
    YSF = 11
    NXDN96 = 12

    def serialize(self):
        return {
            "name": self.name,
            "value": self.value
        }

    @classmethod
    def deserialize(cls, tag: dict):
        return cls[tag["name"]]

class Systems(list):
    def serialize(self):
        systems = []
        for system in self:
            systems.append(system.serialize())
        return systems

    @classmethod
    def deserialize(cls, systems: list):
        self = cls()
        for system in systems:
            self.append(System.deserialize(system))
        return self

    def to_file(self, filename: str):
        systems = self.serialize()
        with open(filename, "w") as f:
            json.dump(systems, f, indent=4)

    @classmethod
    def from_file(cls, filename: str):
        with open(filename, "r") as f:
            systems = json.load(f)
        return cls.deserialize(systems)

class Sites(list):
    def serialize(self):
        sites = []
        for site in self:
            sites.append(site.serialize())
        return sites

    @classmethod
    def deserialize(cls, sites: list):
        self = cls()
        for site in sites:
            self.append(Site.deserialize(site))
        return self

class Talkgroups(list):
    def serialize(self):
        talkgroups = []
        for talkgroup in self:
            talkgroups.append(talkgroup.serialize())
        return talkgroups

    @classmethod
    def deserialize(cls, talkgroups: list):
        self = cls()
        for talkgroup in talkgroups:
            self.append(Talkgroup.deserialize(talkgroup))
        return self

@dataclass
class Talkgroup:
    tg_id: int
    tg_name: str
    tg_tag: Tag

    def serialize(self):
        return {
            "tg_id": self.tg_id,
            "tg_name": self.tg_name,
            "tg_tag": self.tg_tag.serialize()
        }

    @classmethod
    def deserialize(cls, talkgroup: dict):
        return cls(
            tg_id=talkgroup["tg_id"],
            tg_name=talkgroup["tg_name"],
            tg_tag=Tag.deserialize(talkgroup["tg_tag"])
        )

@dataclass
class Site:
    name: str
    site_id: int
    control: list[float]
    channels: list[float]
    lat: float
    long: float
    range: float

    def serialize(self):
        return {
            "name": self.name,
            "site_id": self.site_id,
            "control": self.control,
            "channels": self.channels,
            "lat": self.lat,
            "long": self.long,
            "range": self.range
        }

    @classmethod
    def deserialize(cls, site: dict):
        return cls(
            name=site["name"],
            site_id=site["site_id"],
            control=site["control"],
            channels=site["channels"],
            lat=site["lat"],
            long=site["long"],
            range=site["range"]
        )

@dataclass
class System:
    name: str
    system_id: int
    modulation: Modulation
    talkgroups: Talkgroups
    sites: Sites

    def serialize(self):
        return {
            "name": self.name,
            "system_id": self.system_id,
            "modulation": self.modulation.serialize(),
            "talkgroups": self.talkgroups.serialize(),
            "sites": self.sites.serialize()
        }

    @classmethod
    def deserialize(cls, system: dict):
        return cls(
            name=system["name"],
            system_id=system["system_id"],
            modulation=Modulation.deserialize(system["modulation"]),
            talkgroups=Talkgroups.deserialize(system["talkgroups"]),
            sites=Sites.deserialize(system["sites"])
        )

@dataclass
class Tone:
    tone_type: ToneType
    tone_value: float

    def serialize(self):
        return {
            "tone_type": self.tone_type.serialize(),
            "tone_value": self.tone_value
        }

    @classmethod
    def deserialize(cls, tone: dict):
        return cls(
            tone_type=ToneType.deserialize(tone["tone_type"]),
            tone_value=tone["tone_value"]
        )

@dataclass
class AgencyFreq:
    name: str
    tone: Tone
    freq: float
    tag: Tag
    mode: Mode

    def serialize(self):
        return {
            "name": self.name,
            "tone": self.tone.serialize(),
            "mode": self.mode.serialize(),
            "freq": self.freq,
            "tag": self.tag.serialize()
        }

    @classmethod
    def deserialize(cls, agency_freq):
        return cls(
            name=agency_freq["name"],
            tone=Tone.deserialize(agency_freq["tone"]),
            mode=Mode.deserialize(agency_freq["mode"]),
            freq=agency_freq["freq"],
            tag=Tag.deserialize(agency_freq["tag"])
        )

class AgencyFreqs(list):
    def serialize(self):
        freqs = []
        for freq in self:
            freqs.append(freq.serialize())
        return freqs

    @classmethod
    def deserialize(cls, freqs: list):
        self = cls()
        for freq in freqs:
            self.append(AgencyFreq.deserialize(freq))
        return self

@dataclass
class Agency:
    agency_id: int # subcat id
    county_name: str
    agency_name: str # subcat name
    freqs: AgencyFreqs[AgencyFreq]

    def serialize(self):
        return {
            "agency_id": self.agency_id,
            "county_name": self.county_name,
            "agency_name": self.agency_name,
            "freqs": self.freqs.serialize()
        }

    @classmethod
    def deserialize(cls, agency: dict):
        return cls(
            agency_id=agency["agency_id"],
            county_name=agency["county_name"],
            agency_name=agency["agency_name"],
            freqs=AgencyFreqs.deserialize(agency["freqs"])
        )

class Agencies(list):
    def serialize(self):
        agencies = []
        for agency in self:
            agencies.append(agency.serialize())
        return agencies

    @classmethod
    def deserialize(cls, agencies: list):
        self = cls()
        for agency in agencies:
            self.append(Agency.deserialize(agency))
        return self

    def to_file(self, filename: str):
        agencies = self.serialize()
        with open(filename, "w") as f:
            json.dump(agencies, f, indent=4)

    @classmethod
    def from_file(cls, filename: str):
        with open(filename, "r") as f:
            agencies = json.load(f)
        return cls.deserialize(agencies)

@dataclass
class Database:
    systems: Systems
    agencies: Agencies

    def serialize(self):
        return {
            "systems": self.systems.serialize(),
            "agencies": self.agencies.serialize()
        }

    @classmethod
    def deserialize(cls, database: dict):
        return cls(
            systems=Systems.deserialize(database["systems"]),
            agencies=Agencies.deserialize(database["agencies"])
        )

    def to_file(self, filename: str):
        database = self.serialize()
        with open(filename, "w") as f:
            json.dump(database, f, indent=4)

    @classmethod
    def from_file(cls, filename: str):
        with open(filename, "r") as f:
            agencies = json.load(f)
        return cls.deserialize(agencies)

@dataclass
class Subcat:
    scid: int
    scName: str
    lat: float
    lon: float
    range: float

    def serialize(self):
        return {
            "scid": self.scid,
            "scName": self.scName,
            "lat": self.lat,
            "lon": self.lon,
            "range": self.range
        }

    @classmethod
    def deserialize(cls, subcat: dict):
        return cls(
            scid=subcat["scid"],
            scName=subcat["scName"],
            lat=subcat["lat"],
            lon=subcat["lon"],
            range=subcat["range"]
        )

class RadioReferenceAPI(Client):
    def __init__(self, username: str, password: str):
        super().__init__(wsdl="./schema.xml", settings=Settings(strict=False))
        self.username = username
        self.password = password
        self.auth_info = {
            'appKey': '88969092',
            'username': self.username,
            'password': self.password,
            'version': 'latest',
            'style': 'rpc'
        }
        self.progress: tqdm | None = None

    def get_talkgroups(self, sid: int):
        tgs = self.service.getTrsTalkgroups(
            authInfo=self.auth_info,
            sid=sid,
            tgCid=xsd.Nil,
            tgTag=xsd.Nil,
            tgDec=xsd.Nil
        )
        talkgroups = []
        for tg in tgs:
            tag = Tag.convert_tag(tg.tags[0].tagId)
            talkgroup = Talkgroup(
                tg_id=tg.tgDec,
                tg_name=tg.tgDescr,
                tg_tag=tag
            )
            talkgroups.append(talkgroup)
        return Talkgroups(talkgroups)

    def get_sites(self, sid: int):
        api_sites = self.service.getTrsSites(
            authInfo=self.auth_info,
            sid=sid
        )
        sites = []
        for site in api_sites:
            control = []
            channels = []
            for freq in site.siteFreqs:
                if isinstance(freq.use, str):
                    control.append(float(freq.freq))
                else:
                    channels.append(float(freq.freq))
            site = Site(
                name=site.siteDescr,
                site_id=site.sid,
                control=control,
                channels=channels,
                lat=float(site.lat),
                long=float(site.lon),
                range=float(site.range)
            )
            sites.append(site)
        return Sites(sites)

    def get_all_systems(self, stid: int):
        state_info = self.service.getStateInfo(
            authInfo=self.auth_info,
            stid=stid
        )

        self.progress = tqdm(desc="Progress", total=len(state_info.countyList))

        number = 0
        county_infos = []
        for county in state_info.countyList:
            county_info = self.service.getCountyInfo(
                authInfo=self.auth_info,
                ctid=county.ctid
            )
            number += len(county_info.trsList) + 1
            county_infos.append(county_info)
            self.progress.update(1)

        total = number + len(state_info.trsList)
        self.progress.close()
        self.progress = tqdm(desc="Progress", total=total)

        ids = []
        systems = []
        for county_info in county_infos:
            for system in county_info.trsList:
                if system.sid not in ids:
                    system_info = self.service.getTrsDetails(
                        authInfo=self.auth_info,
                        sid=system.sid
                    )
                    modulation = Modulation.convert_stype(
                        system_info.sType,
                        system_info.sFlavor
                    )
                    sites = self.get_sites(system.sid)
                    talkgroups = self.get_talkgroups(system.sid)

                    system = System(
                        name=system_info.sName,
                        system_id=system.sid,
                        modulation=modulation,
                        talkgroups=talkgroups,
                        sites=sites
                    )
                    systems.append(system)
                    ids.append(system.system_id)

                self.progress.update(1)
            self.progress.update(1)

        for system in state_info.trsList:
            if system.sid not in ids:
                system_info = self.service.getTrsDetails(
                    authInfo=self.auth_info,
                    sid=system.sid
                )

                modulation = Modulation.convert_stype(
                    system_info.sType,
                    system_info.sFlavor
                )
                sites = self.get_sites(system.sid)
                talkgroups = self.get_talkgroups(system.sid)

                system = System(
                    name=system_info.sName,
                    system_id=system.sid,
                    modulation=modulation,
                    talkgroups=talkgroups,
                    sites=sites
                )
                systems.append(system)
                ids.append(system.system_id)
            self.progress.update(1)

        self.progress.close()
        return Systems(systems)

    def get_all_agencies(self, stid: int):
        state_info = self.service.getStateInfo(
            authInfo=self.auth_info,
            stid=stid
        )

        self.progress = tqdm(
            desc="Progress",
            total=len(state_info.countyList) + len(state_info.agencyList)
        )

        counties = {0: state_info.stateName}
        for county in state_info.countyList:
            counties[county.ctid] = county.countyName

        ids = []
        subcats = []
        for county in state_info.countyList:
            county_info = self.service.getCountyInfo(
                authInfo=self.auth_info,
                ctid=county.ctid
            )
            if county_info.agencyList:
                interval = 1 / len(county_info.agencyList)
                for agency in county_info.agencyList:
                    agency_info = self.service.getAgencyInfo(
                        authInfo=self.auth_info,
                        aid=agency.aid
                    )
                    if agency_info.cats:
                        for cat in agency_info.cats:
                            if cat.subcats:
                                for subcat in cat.subcats:
                                    if subcat.scid not in ids:
                                        ids.append(subcat.scid)
                                        subcats.append((subcat, counties[agency_info.ctid]))

                    self.progress.update(interval)
            else:
                self.progress.update(1)

        for agency in state_info.agencyList:
            agency_info = self.service.getAgencyInfo(
                authInfo=self.auth_info,
                aid=agency.aid
            )
            if agency_info.cats:
                for cat in agency_info.cats:
                    if cat.subcats:
                        for subcat in cat.subcats:
                            if subcat.scid not in ids:
                                ids.append(subcat.scid)
                                subcats.append((subcat, counties[agency_info.ctid]))

            self.progress.update(1)

        self.progress.close()
        self.progress = tqdm(desc="Progress", total=len(subcats))

        agencies = []
        for subcat, county_name in subcats:
            freqs = self.service.getSubcatFreqs(
                authInfo=self.auth_info,
                scid=subcat.scid
            )
            agency_freqs = AgencyFreqs([])
            if len(freqs) == 0:
                self.progress.update(1)
                interval = 0
            else:
                interval = 1 / len(freqs)
            for freq in freqs:
                if freq.out:
                    mode = Mode(int(freq.mode))
                    if mode == Mode.P25:
                        self.progress.update(n=interval)
                    elif mode == Mode.DMR:
                        self.progress.update(n=interval)
                    elif mode == Mode.NXDN48:
                        self.progress.update(n=interval)
                    elif mode == Mode.NXDN96:
                        self.progress.update(n=interval)
                    else:
                        if freq.tone:
                            if freq.tone.endswith(" PL"):
                                tone_type = ToneType.CTCSS
                                tone_value = float(freq.tone.replace("PL", ""))
                            elif freq.tone.endswith("DPL"):
                                tone_type = ToneType.DCS
                                tone_value = float(freq.tone.replace("DPL", ""))
                            else:
                                tone_type = ToneType.NONE
                                tone_value = 0
                        else:
                            tone_type = ToneType.NONE
                            tone_value = 0

                        tone = Tone(tone_type, tone_value)
                        tag = Tag.convert_tag(int(freq.tags[0].tagId))

                        agency_freq = AgencyFreq(
                            name=freq.descr,
                            freq=float(freq.out),
                            tone=tone,
                            mode=mode,
                            tag=tag
                        )
                        agency_freqs.append(agency_freq)

                        self.progress.update(n=interval)
                else:
                    self.progress.update(n=1)

            agency = Agency(
                agency_id=subcat.scid,
                county_name=county_name,
                agency_name=subcat.scName,
                freqs=agency_freqs,
            )
            agencies.append(agency)

        return Agencies(agencies)

    def get_database(self, filename: str, stid: int):
        if os.path.exists(filename):
            return Database.from_file(filename)
        else:
            systems = self.get_all_systems(stid)
            agencies = self.get_all_agencies(stid)
            db = Database(systems=systems, agencies=agencies)
            db.to_file(filename)
        return db

    @staticmethod
    def near_point(db: Database, lat1: float, lon1: float, radius: float = 10):
        x1 = lat1 * 69
        y1 = math.cos(lon1) * 69

        new_db = replace(db)
        new_db.systems = []

        for system in db.systems:
            new_system = replace(system)
            new_system.sites = []

            for site in system.sites:
                lat2, lon2 = site.lat, site.long

                x2 = lat2 * 69
                y2 = math.cos(lon2) * 69

                # slope = (y2 - y1) / (x2 - x1)
                distance = math.sqrt(((y2 - y1) ** 2) + ((x2 - x1) ** 2))

                if distance < radius:
                    new_system.sites.append(site)
                    print(site.name)

            if len(new_system.sites) > 0:
                new_db.systems.append(new_system)

        return new_db


    @staticmethod
    def export_sdrtrunk(db: Database, filename: str):
        playlist = ET.Element("playlist", {"version": "4"})
        for system in db.systems:
            for talkgroup in system.talkgroups:
                attrib = {
                    "color": "0",
                    "group": talkgroup.tg_tag.value,
                    "list": system.name,
                    "name": talkgroup.tg_name
                }
                alias = ET.SubElement(playlist, "alias", attrib)
                attrib = {
                    "type": "talkgroup",
                    "protocol": "APCO25",
                    "value": str(talkgroup.tg_id)
                }
                ET.SubElement(alias, "id", attrib)

        for system in db.systems:
            for site in system.sites:
                if len(site.control) == 0:
                    continue
                if system.modulation != Modulation.P25_P1 and system.modulation != Modulation.P25_P2:
                    continue
                attrib = {
                    "system": system.name,
                    "site": site.name,
                    "name": "Control Channels",
                    "order": "0",
                    "enabled": "false"
                }
                channel = ET.SubElement(playlist, "channel", attrib)

                log_config = ET.SubElement(channel, "event_log_configuration")
                log_msg = ET.SubElement(log_config, "logger")
                log_msg.text = "DECODED_MESSAGE"

                ET.SubElement(channel, "aux_decode_configuration")
                ET.SubElement(channel, "record_configuration")

                if len(site.control) > 1:
                    attrib = {
                        "type": "sourceConfigTunerMultipleFrequency",
                        "frequency_rotation_delay": "400",
                        "source_type": "TUNER_MULTIPLE_FREQUENCIES"
                    }
                else:
                    attrib = {
                        "type": "sourceConfigTuner",
                        "frequency": str(int(site.control[0] * 1e6)),
                        "source_type": "TUNER"
                    }

                source_config = ET.SubElement(channel, "source_configuration", attrib)

                if len(site.control) > 1:
                    for freq in site.control:
                        frequency = ET.SubElement(source_config, "frequency")
                        frequency.text = str(int(freq * 1e6))

                if system.modulation == Modulation.P25_P1:
                    attrib = {
                        "type": "decodeConfigP25Phase1",
                        "modulation": "C4FM",
                        "traffic_channel_pool_size": "20",
                        "ignore_data_calls": "false"
                    }
                elif system.modulation == Modulation.P25_P2:
                    attrib = {
                        "type": "decodeConfigP25Phase2",
                        "auto_detect_scramble_parameters": "true",
                        "traffic_channel_pool_size": "20",
                        "ignore_data_calls": "false"
                    }
                else:
                    attrib = {}

                ET.SubElement(channel, "decode_configuration", attrib)

                alias_list = ET.SubElement(channel, "alias_list_name")
                alias_list.text = system.name

        i = 1
        for agency in db.agencies:
            for freq in agency.freqs:
                if freq.mode not in [Mode.FM, Mode.FMN, Mode.AM]:
                    continue

                attrib = {
                    "color": "0",
                    "group": freq.tag.value,
                    "list": "Agencies",
                    "name": freq.name
                }
                alias = ET.SubElement(playlist, "alias", attrib)

                attrib = {
                    "type": "talkgroup",
                    "value": str(i),
                    "protocol": "NBFM" if freq.mode in [Mode.FM, Mode.FMN] else "AM"
                }
                ET.SubElement(alias, "id", attrib)

                if freq.mode == Mode.FM or freq.mode == Mode.FMN:
                    if freq.tone.tone_type == ToneType.DCS:
                        attrib = {
                            "type": "dcs",
                            "code": f"N{int(freq.tone.tone_value):03d}"
                        }
                        ET.SubElement(alias, "id", attrib)

                i += 1

        i = 1
        for agency in db.agencies:
            for freq in agency.freqs:
                if freq.mode not in [Mode.FM, Mode.FMN, Mode.AM]:
                    continue

                attrib = {
                    "system": agency.county_name,
                    "site": agency.agency_name,
                    "name": freq.name,
                    "order": "1",
                    "enabled": "false"
                }
                channel = ET.SubElement(playlist, "channel", attrib)

                if freq.mode == Mode.FM or freq.mode == Mode.FMN:
                    if freq.tone.tone_type == ToneType.DCS:
                        aux_config = ET.SubElement(channel, "aux_decode_configuration")
                        aux_decode = ET.SubElement(aux_config, "aux_decoder")
                        aux_decode.text = "DCS"
                    else:
                        ET.SubElement(channel, "aux_decode_configuration")
                else:
                    ET.SubElement(channel, "aux_decode_configuration")

                ET.SubElement(channel, "record_configuration")
                ET.SubElement(channel, "event_log_configuration")

                attrib = {
                    "type": "sourceConfigTuner",
                    "frequency": str(int(freq.freq * 1e6)),
                    "source_type": "TUNER"
                }
                ET.SubElement(channel, "source_configuration", attrib)

                alias_list = ET.SubElement(channel, "alias_list_name")
                alias_list.text = "Agencies"

                if freq.mode == Mode.FM or freq.mode == Mode.FMN:
                    attrib = {
                        "type": "decodeConfigNBFM",
                        "audioFilter": "true",
                        "bandwidth": "BW_12_5",
                        "squelch": "-78",
                        "autoTrack": "true",
                        "talkgroup": str(i)
                    }
                elif freq.mode == Mode.AM:
                    attrib = {
                        "type": "decodeConfigAM",
                        "bandwidth": "BW_15_0",
                        "squelch": "-78",
                        "autoTrack": "true",
                        "talkgroup": str(i)
                    }
                else:
                    attrib = {}

                ET.SubElement(channel, "decode_configuration", attrib)

                i += 1

        xml = parseString(ET.tostring(playlist))
        xml = xml.toprettyxml()
        with open(filename, "w") as f:
            f.write(xml)


def main():
    # rrapi = RadioReferenceAPI("username", "password")
    # systems = rrapi.get_all_systems(37)
    # systems.to_file("systems.json")
    # rrapi.update_file("systems.json")
    # systems = Systems.from_file("systems.json")
    # rrapi.export_sdrtrunk(systems, "config.xml")
    # agencies = rrapi.get_all_agencies(37)
    # agencies.to_file("agencies.json")
    # agencies = rrapi.get_all_agencies(37)
    # db = Database.from_file("db.json")
    # db = rrapi.near_point(db, 35.052098, -78.712022, radius=25)
    # for system in db.systems:
    #     print(system.name)
    #     for site in system.sites:
    #         print(site.name)

if __name__ == "__main__":
    main()
