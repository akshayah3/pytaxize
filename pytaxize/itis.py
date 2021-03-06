import sys
import requests
import pandas as pd
from lxml import etree

def itis_ping(**kwargs):
    '''
    Ping the ITIS API

    Usage:
    >>> import pytaxize
    >>> pytaxize.itis_ping()
    u'<ns:getDescriptionResponse xmlns:ns="http://itis_service.itis.usgs.gov"><ns:return xmlns:ax21="http://data.itis_service.itis.usgs.gov/xsd" xmlns:ax26="http://itis_service.itis.usgs.gov/xsd" xmlns:ax23="http://metadata.itis_service.itis.usgs.gov/xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:type="ax26:SvcDescription"><ax26:description>This is the ITIS Web Service, providing access to the data behind www.itis.gov. The database contains 641,468 scientific names (486,232 of them valid/accepted) and 118,145 common names.</ax26:description></ns:return></ns:getDescriptionResponse>'
    '''
    tt = _itisGET('getDescription', {}, **kwargs)
    ns = {'ax26':'http://itis_service.itis.usgs.gov/xsd'}
    nodes = tt.xpath('//ax26:description', namespaces=ns)
    text = [x.text for x in nodes][0]
    return text

def getacceptednamesfromtsn(tsn, **kwargs):
    '''
    Get accepted names from tsn
    :param tsn: taxonomic serial number (TSN) (character or numeric)
    Usage:
    # TSN accepted - good name
    pytaxize.getacceptednamesfromtsn('208527')
    # TSN not accepted - input TSN is old name
    pytaxize.getacceptednamesfromtsn('504239')
    '''
    out = _itisGET("getAcceptedNamesFromTSN", {'tsn': tsn}, **kwargs)
    temp = out.getchildren()
    if(temp[0].getchildren()[1].values()[0] == 'true'):
        dat = temp[0].getchildren()[0].text
    else:
        nodes = temp[0].getchildren()[1].getchildren()
        dat = _parse_nodes(nodes)
        dat.pop('author')
        dat['submittedTsn'] = temp[0].getchildren()[0].text
    return dat

def getanymatchcount(x, **kwargs):
    '''
    Get any match count.
    :param x: text or taxonomic serial number (TSN) (character or numeric)
    :param **kwargs: optional additional curl options (debugging tools mostly)
    Usage:
    pytaxize.getanymatchcount(x=202385)
    pytaxize.getanymatchcount(x="dolphin")
    '''
    out = _itisGET("getAnyMatchCount", {'srchKey': x}, **kwargs)
    return int(out.getchildren()[0].text)

def getcommentdetailfromtsn(tsn, **kwargs):
    '''
    Get comment detail from TSN
    :param tsn: TSN for a taxonomic group (numeric)
    :param **kwargs: optional additional curl options (debugging tools mostly)
    Usage:
    pytaxize.getcommentdetailfromtsn(tsn=180543)
    '''
    out = _itisGET("getCommentDetailFromTSN", {'tsn': tsn}, **kwargs)
    ns = {'ax21':'http://data.itis_service.itis.usgs.gov/xsd'}
    matches = ["commentDetail", "commentId", "commentTimeStamp", "commentator","updateDate"]
    colnames = ['comment','commid','commtime','commentator','updatedate']
    return _itisdf(out, ns, matches, colnames)

def getcommonnamesfromtsn(tsn, **kwargs):
    '''
    Get common names from tsn
    :param tsn: TSN for a taxonomic group (numeric)
    :param **kwargs: optional additional curl options (debugging tools mostly)
    Usage:
    pytaxize.getcommonnamesfromtsn(tsn=183833)
    '''
    out = _itisGET("getCommonNamesFromTSN", {'tsn': tsn}, **kwargs)
    ns = {'ax21':'http://data.itis_service.itis.usgs.gov/xsd'}
    matches = ["commonName", "language", "tsn"]
    colnames = ['comname','lang','tsn']
    res = _itisextract(out, ns, matches, colnames)
    del res[2][-1]
    return _array2df(res, colnames)

def getcoremetadatafromtsn(tsn, **kwargs):
    '''
    Get core metadata from tsn
    Usage:
    # coverage and currrency data
    pytaxize.getcoremetadatafromtsn(tsn=28727)
    # no coverage or currrency data
    pytaxize.getcoremetadatafromtsn(tsn=183671)
    '''
    out = _itisGET("getCoreMetadataFromTSN", {'tsn': tsn}, **kwargs)
    ns = {'ax21':'http://data.itis_service.itis.usgs.gov/xsd'}
    toget = ["credRating","rankId","taxonCoverage","taxonCurrency","taxonUsageRating","tsn"]
    return _itis_parse(toget, out, ns)

def getcoveragefromtsn(tsn, **kwargs):
    '''
    Get coverge from tsn
    Usage:
    # coverage data
    pytaxize.getcoveragefromtsn(tsn=28727)
    # no coverage data
    pytaxize.getcoveragefromtsn(526852)
    # combine many results
    import pandas as pd
    pd.concat([ getcoveragefromtsn(x) for x in [28727,526852] ])
    '''
    out = _itisGET("getCoverageFromTSN", {'tsn': tsn}, **kwargs)
    matches = ["rankId", "taxonCoverage", "tsn"]
    df = _itisdf(out, ns21, matches, _tolower(matches))
    return df

def getcredibilityratingfromtsn(tsn, **kwargs):
    '''
    Get credibility rating from tsn
    Usage:
    pytaxize.getcredibilityratingfromtsn(526852)
    pytaxize.getcredibilityratingfromtsn(28727)
    '''
    out = _itisGET("getCredibilityRatingFromTSN", {'tsn': tsn}, **kwargs)
    matches = ["credRating", "tsn"]
    df = _itisdf(out, ns21, matches, _tolower(matches))
    return df

def getcredibilityratings(**kwargs):
    '''
    Get possible credibility ratings
    :param **kwargs: Curl options passed on to \code{\link[httr]{GET}}
    Usage:
    pytaxize.getcredibilityratings()
    '''
    out = _itisGET("getCredibilityRatings", {}, **kwargs)
    nodes = out.xpath("//ax23:credibilityValues", namespaces=ns23)
    credibilityValues = [x.text for x in nodes]
    df = pd.DataFrame(credibilityValues, columns=['credibilityValues'])
    return df

def getcurrencyfromtsn(tsn, **kwargs):
    '''
    Get currency from tsn
    Usage
    # currency data
    pytaxize.getcurrencyfromtsn(28727)
    # no currency dat
    pytaxize.getcurrencyfromtsn(526852)
    '''
    out = _itisGET("getCurrencyFromTSN", {'tsn': tsn}, **kwargs)
    matches = ["rankId","taxonCurrency","tsn"]
    df = _itisdf(out, ns21, matches, _tolower(matches))
    return df

def getdatedatafromtsn(tsn, **kwargs):
    '''
    Get date data from tsn
    Usage
    pytaxize.getdatedatafromtsn(180543)
    '''
    out = _itisGET("getDateDataFromTSN", {'tsn': tsn}, **kwargs)
    matches = ["initialTimeStamp","updateDate","tsn"]
    df = _itisdf(out, ns21, matches, _tolower(matches))
    return df

def getexpertsfromtsn(tsn, **kwargs):
    '''
    Get expert information for the TSN.
    Usage:
    pytaxize.getexpertsfromtsn(180544)
    '''
    out = _itisGET("getExpertsFromTSN", {'tsn': tsn}, **kwargs)
    toget = ["comment","expert","name","referredTsn","referenceFor","updateDate"]
    return _itis_parse(toget, out, ns21)

def gettaxonomicranknamefromtsn(tsn, **kwargs):
    '''
    Returns the kingdom and rank information for the TSN.

    :param tsn: TSN for a taxonomic group (numeric)

    Usage:
    pytaxize.gettaxonomicranknamefromtsn(tsn = 202385)
    '''
    tt = _itisGET('getTaxonomicRankNameFromTSN', {'tsn': tsn}, **kwargs)
    ns = {'ax21':'http://data.itis_service.itis.usgs.gov/xsd'}
    df = _parse2df(tt, ns)
    return df

def getfullhierarchyfromtsn(tsn, **kwargs):
    '''
    Get full hierarchy from tsn

    :param tsn: TSN for a taxonomic group (numeric)

    Usage:
    pytaxize.getfullhierarchyfromtsn(tsn = 37906)
    pytaxize.getfullhierarchyfromtsn(tsn = 100800)
    '''
    tt = _itisGET('getFullHierarchyFromTSN', {'tsn': tsn}, **kwargs)
    df = _parse_hier(tt, ns21)
    return df

def _fullrecord(verb, args, **kwargs):
    out = _itisGET(verb, args, **kwargs)
    toget = ["acceptedNameList","commentList","commonNameList","completenessRating",
               "coreMetadata","credibilityRating","currencyRating","dateData","expertList",
               "geographicDivisionList","hierarchyUp","jurisdictionalOriginList",
               "kingdom","otherSourceList","parentTSN","publicationList","scientificName",
               "synonymList","taxRank","taxonAuthor","unacceptReason","usage"]
    def parsedat(x):
        ch = out.xpath('//ax21:'+x, namespaces=ns21)[0].getchildren()
        return _get_text(ch)
    return [parsedat(x) for x in toget]

def getfullrecordfromlsid(lsid, **kwargs):
    '''
    Returns the full ITIS record for the TSN in the LSID, found by comparing the
    TSN in the search key to the TSN field. Returns an empty result set if
    there is no match or the TSN is invalid.

    :param lsid: lsid for a taxonomic group (character)
    :param **kwargs: optional additional curl options (debugging tools mostly)
    Usage:
    pytaxize.getfullrecordfromlsid("urn:lsid:itis.gov:itis_tsn:180543")
    pytaxize.getfullrecordfromlsid("urn:lsid:itis.gov:itis_tsn:37906")
    pytaxize.getfullrecordfromlsid("urn:lsid:itis.gov:itis_tsn:100800")
    '''
    return _fullrecord("getFullRecordFromLSID", {'lsid': lsid}, **kwargs)

def getfullrecordfromtsn(tsn, **kwargs):
    '''
    Returns the full ITIS record for a TSN
    :param tsn: tsn for a taxonomic group (character)
    :param **kwargs: optional additional curl options (debugging tools mostly)
    Usage:
    pytaxize.getfullrecordfromtsn("504239")
    pytaxize.getfullrecordfromtsn("202385")
    pytaxize.getfullrecordfromtsn("183833")
    '''
    return _fullrecord("getFullRecordFromTSN", {'tsn': tsn}, **kwargs)

def getgeographicdivisionsfromtsn(tsn, **kwargs):
    '''
    Get geographic divisions from tsn
    Usage
    pytaxize.getgeographicdivisionsfromtsn(180543)
    '''
    out = _itisGET("getGeographicDivisionsFromTSN", {'tsn': tsn}, **kwargs)
    toget = ["geographicValue","updateDate"]
    return _itis_parse(toget, out, ns21)

def getgeographicvalues(**kwargs):
    '''
    Get all possible geographic values
    :param **kwargs: Curl options passed on to \code{\link[httr]{GET}}
    Usage
    pytaxize.getgeographicvalues()
    '''
    out = _itisGET("getGeographicValues", {}, **kwargs)
    ns = {'ax21':'http://metadata.itis_service.itis.usgs.gov/xsd'}
    nodes = out.xpath("//ax21:geographicValues", namespaces=ns)
    gv = [x.text for x in nodes]
    return pd.DataFrame(gv, columns=['geographicvalues'])

def getglobalspeciescompletenessfromtsn(tsn, **kwargs):
    '''
    Get global species completeness from tsn
    Usage:
    pytaxize.getglobalspeciescompletenessfromtsn(180541)
    '''
    out = _itisGET("getGlobalSpeciesCompletenessFromTSN", {'tsn': tsn}, **kwargs)
    toget = ["completeness","rankId","tsn"]
    return _itis_parse(toget, out, ns21)


def gethierarchydownfromtsn(tsn, **kwargs):
    '''
    Get hierarchy down from tsn

    :param tsn: TSN for a taxonomic group (numeric)

    Usage:
    pytaxize.gethierarchydownfromtsn(tsn = 161030)
    '''
    tt = _itisGET('getHierarchyDownFromTSN', {'tsn': tsn}, **kwargs)
    ns = {'ax21':'http://data.itis_service.itis.usgs.gov/xsd'}
    df = _parse_hier(tt, ns)
    return df

def gethierarchyupfromtsn(tsn, **kwargs):
    '''
    Get hierarchy up from tsn

    :param tsn: TSN for a taxonomic group (numeric)

    Usage:
    pytaxize.gethierarchyupfromtsn(tsn = 36485)
    pytaxize.gethierarchyupfromtsn(tsn = 37906)
    '''
    tt = _itisGET('getHierarchyUpFromTSN', {'tsn': tsn}, **kwargs)
    ns = {'ax21':'http://data.itis_service.itis.usgs.gov/xsd'}
    df = _parse2df(tt, ns)
    return df

def _itisterms(endpt, args={}, **kwargs):
    '''
    Get itis terms
    Usage:
    pytaxize._itisterms(x="buya")
    '''
    out = _itisGET(endpt, args, **kwargs)

    nodes = out.xpath("//ax21:itisTerms", namespaces=ns21)
    nodes2 = [x.getchildren() for x in nodes]
    allnodes = [[_get_text_single(y) for y in x] for x in nodes2]

    output = []
    for x in allnodes:
        kyz = [y.keys()[0] for y in x]
        notuniq = set([v for v in kyz if kyz.count(v) > 1])
        if len(notuniq) > 0:
            for z in notuniq:
                tt = ','.join([ m.values()[0] for m in x if m.keys()[0] == z ])
                toadd = { z: tt }
                uu = [ v for v in x if v.keys()[0] not in z ]
                uu.append(toadd)
            output.append(uu)
        else:
            output.append(x)

    df = pd.concat([pd.DataFrame([y.values()[0] for y in x]).transpose() for x in output])
    df.columns = [x.keys()[0] for x in allnodes[0]]
    return df

def _get_text_single(x):
    val = [x.text]
    if len(val) > 1:
        aafdsf
    else:
        afadf
    key = [x.tag.split('}')[1]]
    return dict(zip(key, val))

def getitistermsfromcommonname(x, **kwargs):
    '''
    Get itis terms from common names
    Usage:
    pytaxize.getitistermsfromcommonname("buya")
    '''
    return _itisterms(endpt="getITISTermsFromCommonName", args={'srchKey': x}, **kwargs)

def getitisterms(x, **kwargs):
    '''
    Get itis terms
    Usage:
    # fails
    pytaxize.getitisterms("bear")
    '''
    return _itisterms(endpt="getITISTerms", args={'srchKey': x}, **kwargs)

def getitistermsfromscientificname(x, **kwargs):
    '''
    Get itis terms from scientific names
    Usage:
    pytaxize.getitistermsfromscientificname("ursidae")
    pytaxize.getitistermsfromscientificname("Ursus")
    '''
    return _itisterms(endpt="getITISTermsFromScientificName", args={'srchKey': x}, **kwargs)

def itis_hierarchy(tsn=None, what="full"):
    '''
    Get hierarchies from TSN values, full, upstream only, or immediate downstream
    only. Uses the ITIS database.

    :param tsn: One or more TSN's (taxonomic serial number)
    :param what: One of full (full hierarchy), up (immediate upstream), or down
       (immediate downstream)

    Details Note that \code{\link{itis_downstream}} gets taxa downstream to a particular
       rank, whilc this function only gets immediate names downstream.

    Usage:
    # Get full hierarchy
    pytaxize.itis_hierarchy(tsn=180543)

    # Get hierarchy upstream
    pytaxize.itis_hierarchy(tsn=180543, "up")

    # Get hierarchy downstream
    pytaxize.itis_hierarchy(tsn=180543, "down")

    # Many tsn's
    pytaxize.itis_hierarchy(tsn=[180543,41074,36616])
    '''
    tsn2 = convertsingle(tsn)
    temp = []
    if(what == 'full'):
        for i in range(len(tsn2)):
            temp.append(getfullhierarchyfromtsn(tsn2[i]))
    elif(what == 'up'):
        for i in range(len(tsn2)):
            temp.append(gethierarchyupfromtsn(tsn2[i]))
    else:
        for i in range(len(tsn2)):
            temp.append(gethierarchydownfromtsn(tsn2[i]))
    return temp

def getjurisdictionaloriginfromtsn(tsn, **kwargs):
    '''
    Get jurisdictional origin from tsn
    Usage:
    pytaxize.getjurisdictionaloriginfromtsn(180543)
    '''
    out = _itisGET("getJurisdictionalOriginFromTSN", {'tsn': tsn}, **kwargs)
    ns = {'ax21':'http://data.itis_service.itis.usgs.gov/xsd'}
    toget = ["jurisdictionValue","origin","updateDate"]
    return _itis_parse(toget, out, ns)

def getjurisdictionoriginvalues(**kwargs):
    '''
    Get jurisdiction origin values
    Usage:
    pytaxize.getjurisdictionoriginvalues()
    '''
    out = _itisGET("getJurisdictionalOriginValues", {}, **kwargs)
    ns = {'ax23':'http://metadata.itis_service.itis.usgs.gov/xsd'}
    matches = ["jurisdiction","origin"]
    return _itisdf(out, ns, matches, matches, "ax23")

def getjurisdictionvalues(**kwargs):
    '''
    Get possible jurisdiction values
    Usage:
    pytaxize.getjurisdictionvalues()
    '''
    out = _itisGET("getJurisdictionValues", {}, **kwargs)
    ns = {'x23':'http://metadata.itis_service.itis.usgs.gov/xsd'}
    vals = [ x.text for x in out.getchildren()[0].getchildren() ]
    return pd.DataFrame(vals, columns = ['jurisdictionValues'])

def getkingdomnamefromtsn(tsn, **kwargs):
    '''
    Get kingdom names from tsn

    Usage:
    pytaxize.getkingdomnamefromtsn(202385)
    '''
    out = _itisGET("getKingdomNameFromTSN", {'tsn': tsn}, **kwargs)
    ns = {'ax21':"http://data.itis_service.itis.usgs.gov/xsd"}
    toget = ["kingdomId","kingdomName","tsn"]
    return _itis_parse(toget, out, ns)

def getkingdomnames(**kwargs):
    '''
    Get all possible kingdom names

    Usage:
    pytaxize.getkingdomnames()
    '''
    out = _itisGET("getKingdomNames", {}, **kwargs)
    ns = {'ax23':"http://metadata.itis_service.itis.usgs.gov/xsd"}
    matches = ["kingdomId","kingdomName","tsn"]
    return _itisdf(out, ns, matches, _tolower(matches), "ax23")

def getlastchangedate(**kwargs):
    '''
    Provides the date the ITIS database was last updated.

    Usage:
    pytaxize.getlastchangedate()
    '''
    out = _itisGET("getLastChangeDate", {}, **kwargs)
    ns = {'ax23':"http://metadata.itis_service.itis.usgs.gov/xsd"}
    nodes = out.xpath("//ax23:updateDate", namespaces=ns)
    bb = nodes[0].text
    dt = datetime.strptime(bb.split()[0], "%Y-%m-%d")
    return dt

def getlsidfromtsn(tsn, **kwargs):
    '''
    Gets the unique LSID for the TSN, or an empty result if there is no match.

    Usage:
    # valid TSN
    pytaxize.getlsidfromtsn(155166)
    # invalid TSN, returns nothing
    pytaxize.getlsidfromtsn(0)
    '''
    out = _itisGET("getLSIDFromTSN", {'tsn': tsn}, **kwargs)
    tt = out.getchildren()[0].text
    if tt is None:
        tt = "no match"
    else:
        pass
    return tt

def getothersourcesfromtsn(tsn, **kwargs):
    '''
    Returns a list of the other sources used for the TSN.

    Usage:
    pytaxize.getothersourcesfromtsn(182662)
    '''
    out = _itisGET("getOtherSourcesFromTSN", {'tsn': tsn}, **kwargs)
    toget = ["acquisitionDate","name","referredTsn","source",
        "sourceType","updateDate","version"]
    return _itis_parse_2dict(toget, out, ns21)

def getparenttsnfromtsn(tsn, **kwargs):
    '''
    Returns the parent TSN for the entered TSN.

    Usage:
    pytaxize.getparenttsnfromtsn(202385)
    '''
    out = _itisGET("getParentTSNFromTSN", {'tsn': tsn}, **kwargs)
    toget = ["parentTsn","tsn"]
    return _itis_parse(toget, out, ns21)

def getpublicationsfromtsn(tsn, **kwargs):
    '''
    Returns a list of the pulications used for the TSN.

    Usage:
    pytaxize.getpublicationsfromtsn(70340)
    '''
    out = _itisGET("getPublicationsFromTSN", {'tsn': tsn}, **kwargs)
    toget = ["actualPubDate","isbn","issn","listedPubDate","pages",
                "pubComment","pubName","pubPlace","publisher","referenceAuthor",
                "name","refLanguage","referredTsn","title","updateDate"]
    return _itis_parse(toget, out, ns21)

def getranknames(**kwargs):
    '''
    Provides a list of all the unique rank names contained in the database and
    their kingdom and rank ID values.

    Usage:
    pytaxize.getranknames()
    '''
    out = _itisGET("getRankNames", {}, **kwargs)
    matches = ["kingdomName","rankId","rankName"]
    return _itisdf(out, ns23, matches, _tolower(matches), "ax23")

def getrecordfromlsid(lsid, **kwargs):
    '''
    Gets the partial ITIS record for the TSN in the LSID, found by comparing the
    TSN in the search key to the TSN field. Returns an empty result set if
    there is no match or the TSN is invalid.

    Usage:
    pytaxize.getrecordfromlsid("urn:lsid:itis.gov:itis_tsn:180543")
    '''
    out = _itisGET("getRecordFromLSID", {'lsid': lsid}, **kwargs)
    toget = ["authorship","genusPart","infragenericEpithet",
            "infraspecificEpithet","lsid","nameComplete","nomenclaturalCode",
            "rank","rankString","specificEpithet","uninomial","tsn"]
    return _itis_parse(toget, out, ns21)

def getreviewyearfromtsn(tsn, **kwargs):
    '''
    Returns the review year for the TSN.

    Usage:
    pytaxize.getreviewyearfromtsn(180541)
    '''
    out = _itisGET("getReviewYearFromTSN", {'tsn': tsn}, **kwargs)
    toget = ["rankId","reviewYear","tsn"]
    return _itis_parse(toget, out, ns21)

def getscientificnamefromtsn(tsn, **kwargs):
    '''
    Returns the scientific name for the TSN. Also returns the component parts
    (names and indicators) of the scientific name.

    Usage:
    pytaxize.getscientificnamefromtsn(531894)
    '''
    out = _itisGET("getScientificNameFromTSN", {'tsn': tsn}, **kwargs)
    toget = ["combinedName","unitInd1","unitInd3","unitName1","unitName2",
            "unitName3","tsn"]
    return _itis_parse(toget, out, ns21)

# def getsynonymnamesfromtsn(tsn, **kwargs):
#     '''
#     Returns a list of the synonyms (if any) for the TSN.

#     Usage:
#     pytaxize.getsynonymnamesfromtsn(183671) # tsn not accepted
#     pytaxize.getsynonymnamesfromtsn(526852) # tsn accepted
#     '''
#     out = _itisGET("getSynonymNamesFromTSN", {'tsn': tsn}, **kwargs)
#     if len(sapply(nodes, xmlValue)) == 0):
#         name = list("nomatch")
#     else:
#         name = sapply(nodes, xmlValue)
#     nodes = getNodeSet(out, "//ax21:tsn", namespaces=ns21)

#     if len(sapply(nodes, xmlValue)) == 1):
#         tsn = sapply(nodes, xmlValue)
#     else:
#       tsn = sapply(nodes, xmlValue)
#       tsn = tsn[-1]
#     data.frame(name=name, tsn=tsn, stringsAsFactors = FALSE)

def gettaxonauthorshipfromtsn(tsn, **kwargs):
    '''
    Returns the author information for the TSN.

    Usage:
    pytaxize.gettaxonauthorshipfromtsn(183671)
    '''
    out = _itisGET("getTaxonAuthorshipFromTSN", {'tsn': tsn}, **kwargs)
    toget = ["authorship","updateDate","tsn"]
    return _itis_parse(toget, out, ns21)

def gettaxonomicranknamefromtsn(tsn, **kwargs):
    '''
    Returns the kingdom and rank information for the TSN.

    Usage:
    pytaxize.gettaxonomicranknamefromtsn(202385)
    '''
    out = _itisGET("getTaxonomicRankNameFromTSN", {'tsn': tsn}, **kwargs)
    toget = ["kingdomId","kingdomName","rankId","rankName","tsn"]
    return _itis_parse(toget, out, ns21)

def gettaxonomicusagefromtsn(tsn, **kwargs):
    '''
    Returns the usage information for the TSN.

    Usage:
    pytaxize.gettaxonomicusagefromtsn(526852)
    '''
    out = _itisGET("getTaxonomicUsageFromTSN", {'tsn': tsn}, **kwargs)
    toget = ["taxonUsageRating","tsn"]
    return _itis_parse(toget, out, ns21)

def gettsnbyvernacularlanguage(language, **kwargs):
    '''
    Get tsn by vernacular language not the international language code (character)

    Usage:
    pytaxize.gettsnbyvernacularlanguage("french")
    '''
    out = _itisGET("getTsnByVernacularLanguage", {'language': language}, **kwargs)
    matches = ["commonName","language","tsn"]
    return _itisdf(out, ns21, matches, _tolower(matches))

def gettsnfromlsid(lsid, **kwargs):
    '''
    Gets the TSN corresponding to the LSID, or an empty result if there is no match.

    Usage:
    pytaxize.gettsnfromlsid(lsid="urn:lsid:itis.gov:itis_tsn:28726")
    pytaxize.gettsnfromlsid("urn:lsid:itis.gov:itis_tsn:0")
    '''
    out = _itisGET("getTSNFromLSID", {'lsid': lsid}, **kwargs)
    tt = out.getchildren()[0].text
    if tt is None:
        tt = "no match"
    else:
        pass
    return tt

def getunacceptabilityreasonfromtsn(tsn, **kwargs):
    '''
    Returns the unacceptability reason, if any, for the TSN.

    Usage:
    pytaxize.getunacceptabilityreasonfromtsn(183671)
    '''
    out = _itisGET("getUnacceptabilityReasonFromTSN", {'tsn': tsn}, **kwargs)
    toget = ["tsn","unacceptReason"]
    return _itis_parse(toget, out, ns21)

def getvernacularlanguages(**kwargs):
    '''
    Provides a list of the unique languages used in the vernacular table.

    Usage:
    pytaxize.getvernacularlanguages()
    '''
    out = _itisGET("getVernacularLanguages", {}, **kwargs)
    matches = ["languageNames"]
    return _itisdf(out, ns23, matches, _tolower(matches), "ax23")

def searchbycommonname(x, **kwargs):
    '''
    Search for tsn by common name
    Usage:
    pytaxize.searchbycommonname(x="american bullfrog")
    pytaxize.searchbycommonname("ferret-badger")
    pytaxize.searchbycommonname("polar bear")
    '''
    out = _itisGET("searchByCommonName", {'srchKey': x}, **kwargs)
    matches = ["commonName","language","tsn"]
    tmp = out.xpath('//ax21:commonNames', namespaces=ns21)
    return _itisdf(tmp[0], ns21, matches, _tolower(matches))

def searchbycommonnamebeginswith(x, **kwargs):
    '''
    Search for tsn by common name beginning with

    Usage:
    pytaxize.searchbycommonnamebeginswith("inch")
    '''
    out = _itisGET("searchByCommonNameBeginsWith", {'srchKey': x}, **kwargs)
    matches = ["commonName","language","tsn"]
    tmp = out.xpath('//ax21:commonNames', namespaces=ns21)
    return _itisdf(tmp[0], ns21, matches, _tolower(matches))

def searchbycommonnameendswith(x, **kwargs):
    '''
    Search for tsn by common name ending with

    Usage:
    pytaxize.searchbycommonnameendswith("snake")
    '''
    out = _itisGET("searchByCommonNameEndsWith", {'srchKey': x}, **kwargs)
    matches = ["commonName","language","tsn"]
    tmp = out.xpath('//ax21:commonNames', namespaces=ns21)
    return _itisdf(tmp[0], ns21, matches, _tolower(matches))

def itis_searchcommon(x, which = "begin", **kwargs):
    '''
    Searches common name and acts as thin wrapper around
    `searchbycommonnamebeginswith` and `searchbycommonnameendswith`

    pytaxize.itis_searchcommon("inch")
    pytaxize.itis_searchcommon("inch", which = "end")
    '''
    if which == "begin":
        return searchbycommonnamebeginswith(x, **kwargs)
    else:
        return searchbycommonnameendswith(x, **kwargs)

def searchbyscientificname(x, **kwargs):
    '''
    Search by scientific name

    Usage:
    pytaxize.searchbyscientificname(x="Tardigrada")
    pytaxize.searchbyscientificname("Quercus douglasii")
    '''
    out = _itisGET("searchByScientificName", {'srchKey': x}, **kwargs)
    matches = ["combinedName","tsn"]
    return _itisdf(out, ns21, matches, _tolower(matches))

def searchforanymatch(x, **kwargs):
    '''
    Search for any match

    pytaxize.searchforanymatch(x=202385)
    pytaxize.searchforanymatch(x="dolphin")
    '''
    out = _itisGET("searchForAnyMatch", {'srchKey': x}, **kwargs)
    # if isinstance(x, basestring):
    tmp = out.getchildren()[0].getchildren()
    output = []
    for v in tmp:
        tmp = v.getchildren()
        for w in tmp:
            output.append(dict(zip([gettag(e) for e in w.iter()], [e.text for e in w.iter()])))
    return output

def searchforanymatchpaged(x, pagesize, pagenum, ascend, **kwargs):
    '''
    Search for any matched page for descending (logical)

    Usage:
    pytaxize.searchforanymatchpaged(x=202385, pagesize=100, pagenum=1, ascend=False)
    pytaxize.searchforanymatchpaged("Zy", pagesize=100, pagenum=1, ascend=False)
    '''
    args = {'srchKey':x, 'pageSize':pagesize, 'pageNum':pagenum, 'ascend':ascend}
    out = _itisGET("searchForAnyMatchPaged", args, **kwargs)
    tmp = out.getchildren()[0].getchildren()
    output = []
    for v in tmp:
        tmp = v.getchildren()
        for w in tmp:
            output.append(dict(zip([gettag(e) for e in w.iter()], [e.text for e in w.iter()])))
    return output

## helper functions and variables
def convertsingle(x):
    if(x.__class__.__name__ == 'int'):
        return [x]
    else:
        return x

itis_base = 'http://www.itis.gov/ITISWebService/services/ITISService/'
ns21 = {'ax21':'http://data.itis_service.itis.usgs.gov/xsd'}
ns23 = {'ax23':'http://metadata.itis_service.itis.usgs.gov/xsd'}

def _itisGET(endpt, payload, **kwargs):
    out = requests.get(itis_base+endpt, params = payload, **kwargs)
    out.raise_for_status()
    xmlparser = etree.XMLParser()
    tt = etree.fromstring(out.content, xmlparser)
    return tt

def _parse2df(obj, ns):
    nodes = obj.xpath('//ax21:*', namespaces=ns)
    vals = [x.text for x in nodes]
    keys = [x.tag.split('}')[1] for x in nodes]
    df = pd.DataFrame([dict(zip(keys, vals))])
    return df

def _parse_nodes(obj):
    vals = [x.text for x in obj]
    keys = [x.tag.split('}')[1] for x in obj]
    return dict(zip(keys, vals))

def _parse_hier(obj, ns):
    nodes = obj.xpath('//ax21:hierarchyList', namespaces=ns)
    uu = []
    for i in range(len(nodes)):
        uu.append([x.text for x in nodes[i]])
    df = pd.DataFrame(uu, columns=['tsn','author','parentName','parentTsn','rankName','taxonName'])
    df = df.drop('author', axis=1)
    df = df.reindex_axis(['tsn','rankName','taxonName','parentName','parentTsn'], axis=1)
    return df

def _itisdf(a, b, matches, colnames, pastens="ax21"):
    prefix = '//%s:' % pastens
    matches = [prefix+x for x in matches]
    output = []
    for m in matches:
        nodes = a.xpath(m, namespaces=b)
        output.append([x.text for x in nodes])
    df = pd.DataFrame(dict(zip(colnames, output)))
    return df

def _itisextract(a, b, matches, colnames, pastens="ax21"):
    prefix = '//%s:' % pastens
    matches = [prefix+x for x in matches]
    output = []
    for m in matches:
        nodes = a.xpath(m, namespaces=b)
        output.append([x.text for x in nodes])
    return output

def _array2df(obj, colnames):
    if all([len(x)==2 for x in obj]):
        df = pd.DataFrame(dict(zip(colnames, obj)))
    else:
        df = pd.DataFrame([dict(zip(colnames, obj))])
    return df

def _itis_parse(a, b, d):
    def xpathfunc(x, y, nsp):
        tmp = y.xpath("//ax21:"+x, namespaces=nsp)
        return [x.text for x in tmp]
    vals = [xpathfunc(x, b, d) for x in a]
    df = pd.DataFrame(dict(zip(_tolower(a), vals)))
    return df

def _itis_parse_2dict(a, b, d):
    def xpathfunc(x, y, nsp):
        tmp = y.xpath("//ax21:"+x, namespaces=nsp)
        return [x.text for x in tmp]
    vals = [xpathfunc(x, b, d) for x in a]
    return dict(zip(a, vals))

def _get_text(y):
    vals = [x.text for x in y]
    keys = [x.tag.split('}')[1] for x in y]
    return dict(zip(keys, vals))

def _get_text_single(x):
    vals = [x.text]
    keys = [x.tag.split('}')[1]]
    return dict(zip(keys, vals))

def _tolower(y):
    return [x.lower() for x in y]

def gettag(y):
    return y.tag.split('}')[1]

if __name__ == "__main__":
    import doctest
    doctest.testmod()
