<?xml version="1.0"?>
<xsl:stylesheet version="1.0"
  xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
  xmlns:odm="http://www.cdisc.org/ns/odm/v1.3"
  xmlns:osb="http://openstudybuilder.org"
  xmlns:office="urn:schemas-microsoft-com:office:office"
  xmlns:word="urn:schemas-microsoft-com:office:word"
  xmlns="http://www.w3.org/TR/REC-html40">

  <xsl:output method="html" />
  <xsl:template match="/">
    <html>
      <head>
        <meta charset="UTF-8" />
        <link rel="stylesheet"
          href="https://maxcdn.bootstrapcdn.com/bootstrap/3.4.1/css/bootstrap.min.css" />
        <title>
          <xsl:value-of select="/ODM/Study/@OID" />
        </title>
        <style>
          body {
          font-family: Arial;
          background-color: #ffffff;
          margin: 10px;
          }

          h1, h2, h3, h4, h5 {
          margin-top: 3px;
          margin-bottom: 3px;
          padding: 5px;
          }

          .badge {
          display: inline-block;
          margin: 0.2em;
          padding: 0.25em 0.4em;
          font-size: 80%;
          font-weight: 550;
          line-height: 1;
          text-align: center;
          width: auto;
          white-space: normal;
          vertical-align: baseline;
          border-radius: 0px;
          transition: color .15s ease-in-out,background-color .15s ease-in-out,border-color .15s
    ease-in-out,box-shadow .15s ease-in-out;
          }

          .badge-ig {
          display: inline-block;
          margin: 0.2em;
          padding: 0.25em 0.4em;
          font-size: 90%;
          font-weight: 600;
          line-height: 1;
          text-align: center;
          width: auto;
          white-space: normal;
          vertical-align: baseline;
          border-radius: 0px;
          transition: color .15s ease-in-out,background-color .15s ease-in-out,border-color .15s
    ease-in-out,box-shadow .15s ease-in-out;
          }

          @media print {
          .page-break {
          page-break-before: always; /* For older browsers */
          break-before: page; /* Modern spec */
          }
          thead { display: table-header-group; }
          tfoot { display: table-footer-group; }
          .repeat-on-each-page { display: table-row-group; }
          }

          @page Section1 {size:841.7pt 595.45pt;mso-page-orientation:landscape;margin:1.25in 1.0in
    1.25in 1.0in;mso-header-margin:.5in;mso-footer-margin:.5in;mso-paper-source:0;}
          div.Section2 {page:Section2;}
        </style>
      </head>
      <body>
        <div class="Section1">
          <table style="border-collapse: collapse; width: 100%; margin: 0 auto; background: #fff;">
            <tbody>
              <div class="d-print-none">
                <button type="button" class="btn btn-primary btn-sm" data-toggle="collapse"
                  data-target=".Cdash">Cdash</button>&#160; <button type="button"
                  class="btn btn-primary btn-sm" data-toggle="collapse" data-target=".Sdtm">SDTM</button>
    &#160; <button type="button" class="btn btn-primary btn-sm"
                  data-toggle="collapse" data-target=".TopicCode">TopicCode</button>&#160; <button
                  type="button" class="btn btn-primary btn-sm" data-toggle="collapse"
                  data-target=".AdamCode">AdamCode</button>
              </div>
              <xsl:apply-templates select="/ODM/Study/MetaDataVersion/FormDef" />
            </tbody>
          </table>
        </div>
      </body>
      <script src="https://code.jquery.com/jquery-3.3.1.slim.min.js"
        integrity="sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo"
        crossorigin="anonymous"></script>
      <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js"
        integrity="sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz"
        crossorigin="anonymous"></script>
      <script src="https://maxcdn.bootstrapcdn.com/bootstrap/3.4.1/js/bootstrap.min.js"></script>
    </html>
  </xsl:template>

  <xsl:template match="ItemDef">
    <xsl:param name="domainBckg" />

    <xsl:variable name="trBckg">
      <xsl:choose>
        <xsl:when test="//ItemGroupDef/ItemRef[@ItemOID = current()/@OID]/@Mandatory = 'Yes'">
          <xsl:value-of select="'background-color:#E7E6E6; color:#000000;'" />
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="'background-color:#AEAAAA; color:#008000;'" />
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>

    <tr
      style="{$trBckg}">
      <xsl:choose>
        <xsl:when test="./@DataType = 'comment'">
          <td colspan="5" style="border: 1px solid #fff; padding: 5px; width:100%;">
            <h4>
              <xsl:value-of select="@Name" />
            </h4>
          </td>
        </xsl:when>
        <xsl:otherwise>
          <td style="border: 1px solid #fff; padding: 5px; width:5%;">
            <xsl:if test="//ItemGroupDef/ItemRef[@ItemOID = current()/@OID]/@Mandatory = 'Yes'">
              <em>&#160;*&#160;</em>
            </xsl:if>
          </td>
          <td
            style="border: 1px solid #fff; padding: 6px 12px; width:30%;">
            <xsl:value-of select="@Name" />
            <xsl:for-each select="./Alias[@Context = 'TopicCode']">
              <xsl:call-template name="Alias">
                <xsl:with-param name="aliasContext" select="@Context" />
                <xsl:with-param name="aliasName" select="@Name" />
                <xsl:with-param name="aliasBgcolor" select="'#3496f0'" />
              </xsl:call-template>
            </xsl:for-each>
            <xsl:for-each select="./Alias[@Context = 'AdamCode']">
              <xsl:call-template name="Alias">
                <xsl:with-param name="aliasContext" select="@Context" />
                <xsl:with-param name="aliasName" select="@Name" />
                <xsl:with-param name="aliasBgcolor" select="'#2f2f2f'" />
              </xsl:call-template>
            </xsl:for-each>
          </td>
          <td
            style="border: 1px solid #fff; padding: 6px 12px; width:30%;">
            <!-- A CodeList -->
            <xsl:for-each select="CodeListRef">
              <xsl:for-each select="//CodeList[@OID = current()/@CodeListOID]/CodeListItem">
                <xsl:sort select="@OrderNumber" data-type="number" order="ascending" />
                <div><span
                    style='font-size:30px;'>&#9675;</span>&#160;<xsl:value-of select="@osb:name" />
    &#160;</div>
              </xsl:for-each>
              <xsl:for-each
                select="//CodeList[@OID = current()/@CodeListOID]/EnumeratedItem">
                <xsl:sort select="@OrderNumber" data-type="number" order="ascending" />
                <div><span
                    style='font-size:30px;'>&#9675;</span>&#160;<xsl:value-of select="@osb:name" />
    &#160;</div>
              </xsl:for-each>
            </xsl:for-each>
            <xsl:for-each select="./Alias[@Context = 'wordFormat']">
              <xsl:value-of disable-output-escaping="yes" select="@Name" />&#160; </xsl:for-each>
          </td>
          <td
            style="border: 1px solid #fff; padding: 6px 12px; width:30%;">
            <h5>
              <xsl:call-template name="splitter">
                <xsl:with-param name="aliasContext" select="'Sdtm'" />
                <xsl:with-param name="remaining-string" select="@SDSVarName" />
                <xsl:with-param name="pattern" select="'|'" />
                <xsl:with-param name="domainbgcolor" select="$domainBckg" />
              </xsl:call-template>
              <xsl:for-each select="./Alias[@Context = 'Cdash']">
                <xsl:call-template name="splitter">
                  <xsl:with-param name="aliasContext" select="@Context" />
                  <xsl:with-param name="remaining-string" select="./@Name" />
                  <xsl:with-param name="pattern" select="'|'" />
                  <xsl:with-param name="domainbgcolor" select="$domainBckg" />
                </xsl:call-template>
              </xsl:for-each>
              <xsl:for-each select="./Alias[@Context = 'Sdtm']">
                <xsl:call-template name="splitter">
                  <xsl:with-param name="aliasContext" select="@Context" />
                  <xsl:with-param name="remaining-string" select="./@Name" />
                  <xsl:with-param name="pattern" select="'|'" />
                  <xsl:with-param name="domainbgcolor" select="$domainBckg" />
                </xsl:call-template>
              </xsl:for-each>
            </h5>
          </td>
          <td
            style="border: 1px solid #fff; padding: 6px 12px; width:10%;">
            <xsl:for-each select="./Alias[@Context = 'ctdmIntegration']">
              <xsl:value-of disable-output-escaping="yes" select="@Name" />
            </xsl:for-each>
          </td>
        </xsl:otherwise>
      </xsl:choose>
    </tr>
  </xsl:template>

  <xsl:template match="ItemGroupDef">
    <xsl:variable name="domainLevel"
      select="../FormDef/ItemGroupRef[@ItemGroupOID = current()/@OID]/@OrderNumber+1" />
    <xsl:variable
      name="domainBg">
      <xsl:choose>
        <xsl:when test="./@Domain">
          <xsl:for-each select="./osb:DomainColor">
            <xsl:value-of select="." />
          </xsl:for-each>
        </xsl:when>
        <xsl:when test="./Alias/@Context">
          <xsl:for-each select="./Alias/@Context">
            <xsl:choose>
              <xsl:when test="contains(./@Name, 'Note')">
                <xsl:value-of select="substring-after('Note:',@Name)" />
                <xsl:value-of
                  select="':#ffffff !important;'" />
              </xsl:when>
              <xsl:when test="position() = 5">
                <xsl:value-of select="substring(@Name,1,2)" />
                <xsl:value-of
                  select="':#0053ad !important;'" />
              </xsl:when>
              <xsl:when test="position() = 4">
                <xsl:value-of select="substring(@Name,1,2)" />
                <xsl:value-of
                  select="':#ffbf9c !important;'" />
              </xsl:when>
              <xsl:when test="position() = 3">
                <xsl:value-of select="substring(@Name,1,2)" />
                <xsl:value-of
                  select="':#96ff96 !important;'" />
              </xsl:when>
              <xsl:when test="position() = 2">
                <xsl:value-of select="substring(@Name,1,2)" />
                <xsl:value-of
                  select="':#ffff96 !important;'" />
              </xsl:when>
              <xsl:when test="position() = 1">
                <xsl:value-of select="substring(@Name,1,2)" />
                <xsl:value-of
                  select="':#bfffff !important;'" />
              </xsl:when>
              <xsl:otherwise>
                <xsl:value-of select="substring(@Name,1,2)" />
                <xsl:value-of
                  select="':#96ff96 !important;'" />
              </xsl:otherwise>
            </xsl:choose>
          </xsl:for-each>
        </xsl:when>
      </xsl:choose>
    </xsl:variable>
    <tr
      style="background: #1a3172; color: #ffffff;">
      <th colspan="3" style="text-align: left;"><!-- Name of the ItemGroup -->
        <h4>
          <xsl:value-of disable-output-escaping="yes" select="@Name" />
          <xsl:if test="//FormDef/ItemGroupRef[@ItemGroupOID = current()/@OID]/@Mandatory = 'Yes'">
            <em>&#160;*&#160;</em>
          </xsl:if>
        </h4>
      </th>
      <th colspan="2" style="text-align: right;">
        <xsl:for-each select="./Alias[@Context = 'IgType']">
          <xsl:value-of disable-output-escaping="yes" select="@Name" />
        </xsl:for-each>
        <xsl:if test="./@Domain">
          <h4>
            <xsl:call-template name="IGsplitter">
              <xsl:with-param name="aliasContext" select="'Sdtm'" />
              <xsl:with-param name="remaining-string" select="./@Domain" />
              <xsl:with-param name="pattern" select="'|'" />
              <xsl:with-param name="domainbgcolor" select="$domainBg" />
            </xsl:call-template>
          </h4>
        </xsl:if>
      </th>
    </tr>
    <tr>
      <td>
        <!-- For each Item in an ItemGroup in a Form -->
        <xsl:for-each select="ItemRef">
          <xsl:sort select="@OrderNumber" data-type="number" />
          <xsl:apply-templates
            select="//ItemDef[@OID = current()/@ItemOID]">
            <xsl:with-param name="domainBckg" select="$domainBg" />
          </xsl:apply-templates>
        </xsl:for-each>
      </td>
    </tr>
    <tr>
      <td>
        &#160;
      </td>
    </tr>
  </xsl:template>

  <xsl:template match="FormDef">
    <thead>
      <tr style="repeat-on-each-page padding: 6px 12px;">
        <td colspan="5" style="background: #ffffff;">
          <h2>
            <xsl:value-of select="@Name" /><!-- Name of the Form -->
          </h2>
        </td>
      </tr>
    </thead>
      <xsl:choose>
      <xsl:when test="./@osb:sponsorInstruction != 'None'">
        <tr>
          <td colspan="5" style="border: 1px solid #ccc; background: #BDD6EE; color: #000000;">
            <h4>
              Design Notes
            </h4>
          </td>
        </tr>
          <tr>
          <td colspan="5" style="border: 1px solid #ccc; padding: 4px 4px; background: #ffffff;">
            <xsl:value-of disable-output-escaping="yes" select="@osb:sponsorInstruction" />
          </td>
        </tr>
      </xsl:when>
    </xsl:choose>
      <tr
      style="background-color:#ECECEC;">
      <td colspan="4" style="border: 1px solid #fff; padding: 6px 12px;">
        Study ID: NNXXXX-XXXX
      </td>
      <td style="border: 1px solid #fff; padding: 6px 12px;">
        Integration
      </td>
    </tr>
    <!-- For each ItemGroup in the Form -->
      <xsl:for-each select="ItemGroupRef">
      <xsl:sort select="current()/@OrderNumber" data-type="number" />
        <xsl:apply-templates
        select="//ItemGroupDef[@OID = current()/@ItemGroupOID]" />
    </xsl:for-each>
        <tr
      style="background-color:#ffffff;">
      <td colspan="5" style="border: 1px solid #fff; padding: 6px 12px;">
        <xsl:for-each select="./Alias[@Context = 'Oracle']">
          <xsl:value-of disable-output-escaping="yes" select="@Name" />
        </xsl:for-each>
      </td>
    </tr>
  </xsl:template>

  <!-- TEMPLATES -->

  <xsl:template match="Question">
    <xsl:param name="lockItem" />
        <xsl:param name="sdvItem" />
        <xsl:param name="mandatoryItem" />
        <xsl:value-of
      select="TranslatedText" />&#160; <xsl:choose>
      <xsl:when test="($lockItem = 'Yes') and ($sdvItem = 'Yes')">
        <span class="material-symbols-outlined">lock</span>&#160;<span
          class="material-symbols-outlined">account_tree</span>
      </xsl:when>
      <xsl:when test="$lockItem = 'Yes'">
        <span class="material-symbols-outlined">lock</span>
      </xsl:when>
      <xsl:when test="$sdvItem = 'Yes'">
        <span class="material-symbols-outlined">account_tree</span>
      </xsl:when>
      <xsl:otherwise> </xsl:otherwise>
    </xsl:choose>
  </xsl:template>

  <xsl:template match="Decode">
    <xsl:value-of select="TranslatedText" />
  </xsl:template>

  <xsl:template name="Alias">
    <xsl:param name="aliasContext" />
        <xsl:param name="aliasName" />
        <xsl:param name="aliasBgcolor" />
        <div
      class="{$aliasContext} collapse">
      <div class="badge"
        style="background-color:{$aliasBgcolor} !important; border: 1px solid #000; color: white !important;">
        <xsl:value-of disable-output-escaping="yes" select="$aliasName" />
      </div>
    </div>
  </xsl:template>

  <xsl:template name="IGsplitter">
    <xsl:param name="aliasContext" />
        <xsl:param name="remaining-string" />
        <xsl:param name="pattern" />
        <xsl:param
      name="domainbgcolor" />
        <xsl:variable name="itemBg">
      <xsl:choose>
        <xsl:when test="contains($domainbgcolor, substring($remaining-string,1,2))">
          <xsl:value-of select="substring-after($domainbgcolor,substring($remaining-string,1,3))" />
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="'#bfffff !important;'" />
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
        <div
      class="{$aliasContext} collapse">
      <xsl:choose>
        <xsl:when test="contains($remaining-string,$pattern)">
          <split-item>
            <xsl:choose>
              <xsl:when test="contains($remaining-string,'Note:')">
                <span class="badge-ig"
                  style="border: 1px dotted #000; color:black; background-color:#ffffff !important;">
                  <xsl:value-of select="normalize-space($remaining-string,$pattern)" />
                </span>
              </xsl:when>
              <xsl:otherwise>
                <span class="badge-ig"
                  style="border: 1px solid #000; color:black; background-color:{$itemBg} !important!">
                  <xsl:value-of
                    select="normalize-space(concat(substring-before(substring-before($remaining-string,$pattern),':'),' (', substring-after(substring-before($remaining-string,$pattern),':'),')'))" />
                </span>
              </xsl:otherwise>
            </xsl:choose>
          </split-item>
              <xsl:call-template
            name="IGsplitter">
            <xsl:with-param name="aliasContext" select="$aliasContext" />
            <xsl:with-param name="remaining-string"
              select="substring-after($remaining-string,$pattern)" />
            <xsl:with-param name="pattern" select="$pattern" />
            <xsl:with-param name="domainbgcolor" select="$itemBg" />
          </xsl:call-template>
        </xsl:when>
        <xsl:otherwise>
          <split-item>
            <xsl:choose>
              <xsl:when test="contains($remaining-string,'Note:')">
                <span class="badge-ig"
                  style="border: 1px dotted #000; color:black; background-color:#ffffff !important;">
                  <xsl:value-of select="normalize-space($remaining-string)" />
                </span>
              </xsl:when>
              <xsl:when test="contains($remaining-string,'NOT SUBMITTED')">
                <span class="badge-ig"
                  style="border: 1px dotted #000; color:black; background-color:#ffffff !important;">
                  <xsl:value-of select="normalize-space($remaining-string)" />
                </span>
              </xsl:when>
              <xsl:when test="$remaining-string != ''">
                <span class="badge-ig"
                  style="border: 1px solid #000; color:black; background-color:{$itemBg} !important;">
                  <xsl:value-of
                    select="normalize-space(concat(substring-before($remaining-string,':'),' (', substring-after($remaining-string,':'),')'))" />
                </span>
              </xsl:when>
              <xsl:otherwise> </xsl:otherwise>
            </xsl:choose>
          </split-item>
        </xsl:otherwise>
      </xsl:choose>
    </div>
  </xsl:template>

  <xsl:template name="splitter">
    <xsl:param name="aliasContext" />
        <xsl:param name="remaining-string" />
        <xsl:param name="pattern" />
        <xsl:param
      name="domainbgcolor" />
        <xsl:variable name="itemBg">
      <xsl:choose>
        <xsl:when test="contains($remaining-string,'Note')">
          <xsl:value-of select="'#ffffff !important;'" />
        </xsl:when>
        <xsl:when test="contains($domainbgcolor, substring($remaining-string,1,2))">
          <xsl:value-of
            select="substring(substring-after($domainbgcolor,substring($remaining-string,1,2)),2,8)" />
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="'#ffbfaa !important;'" />
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
        <xsl:variable
      name="remainingstrg">
      <xsl:choose>
        <xsl:when test="contains($remaining-string,':')">
          <xsl:value-of select="substring-after($remaining-string,':')" />
        </xsl:when>
        <xsl:otherwise>
          <xsl:value-of select="$remaining-string" />
        </xsl:otherwise>
      </xsl:choose>
    </xsl:variable>
        <div
      class="{$aliasContext} collapse text-left">
      <xsl:choose>
        <xsl:when test="contains($remainingstrg,$pattern)">
          <split-item>
            <xsl:choose>
              <xsl:when test="contains($remaining-string,'Note')">
                <span class="badge"
                  style="border: 1px dotted #000; color:black; background-color:{$itemBg} !important;">
                  <xsl:value-of select="normalize-space(substring-before($remainingstrg,$pattern))" />
                </span>
              </xsl:when>
              <xsl:otherwise>
                <span class="badge"
                  style="border: 1px solid #000; color:black; background-color:{$itemBg}! important;">
                  <xsl:value-of select="normalize-space(substring-before($remainingstrg,$pattern))" />
                </span>
              </xsl:otherwise>
            </xsl:choose>
          </split-item>
              <xsl:call-template
            name="splitter">
            <xsl:with-param name="aliasContext" select="$aliasContext" />
            <xsl:with-param name="remaining-string"
              select="substring-after($remainingstrg,$pattern)" />
            <xsl:with-param name="pattern" select="$pattern" />
            <xsl:with-param name="domainbgcolor" select="$domainbgcolor" />
          </xsl:call-template>
        </xsl:when>
        <xsl:otherwise>
          <split-item>
            <xsl:choose>
              <xsl:when test="contains($remaining-string,'Note')">
                <span class="badge"
                  style="border: 1px dotted #000; color:black; background-color:{$itemBg} !important;">
                  <xsl:value-of select="normalize-space($remainingstrg)" />
                </span>
              </xsl:when>
              <xsl:when test="contains($remaining-string,'NOT SUBMITTED')">
                <span class="badge"
                  style="border: 1px dotted #000; color:black; background-color:#ffffff !important;">
                  <xsl:value-of select="normalize-space($remainingstrg)" />
                </span>
              </xsl:when>
              <xsl:otherwise>
                <span class="badge"
                  style="border: 1px solid #000; color:black; background-color:{$itemBg} !important;">
                  <xsl:value-of select="normalize-space($remainingstrg)" />
                </span>
              </xsl:otherwise>
            </xsl:choose>
          </split-item>
        </xsl:otherwise>
      </xsl:choose>
    </div>
  </xsl:template>

</xsl:stylesheet>