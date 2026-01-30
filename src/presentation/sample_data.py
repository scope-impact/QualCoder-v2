"""
Sample data providers for development and testing.

These functions create mock DTOs for UI development without needing
real data sources.
"""

from design_system import get_colors

from .dto import (
    FileDTO,
    CodeDTO,
    CodeCategoryDTO,
    DocumentDTO,
    DocumentStatsDTO,
    SelectedCodeDTO,
    OverlappingSegmentDTO,
    FileMemoDTO,
    NavigationDTO,
    TextCodingDataDTO,
)


def create_sample_text_coding_data() -> TextCodingDataDTO:
    """Create sample data for the text coding screen."""
    colors = get_colors()

    files = [
        FileDTO(id="1", name="Blur - Girls & Boys.mp3.transcribed", file_type="text", meta="Text - 2.4 KB - 3 codes"),
        FileDTO(id="2", name="ID1.docx", file_type="text", meta="Text - 3.1 KB - 7 codes"),
        FileDTO(id="3", name="ID2.odt", file_type="text", meta="Text - 1.2 KB - 5 codes", selected=True),
        FileDTO(id="4", name="ID3_interview.txt", file_type="text", meta="Text - 8.5 KB - 12 codes"),
    ]

    categories = [
        CodeCategoryDTO(
            id="cat1",
            name="Abilities",
            codes=[
                CodeDTO(id="c1", name="soccer playing", color=colors.code_yellow, count=3),
                CodeDTO(id="c2", name="struggling", color=colors.code_red, count=5),
                CodeDTO(id="c3", name="tactics", color=colors.code_purple, count=2),
            ]
        ),
        CodeCategoryDTO(
            id="cat2",
            name="Opinion of Club",
            codes=[
                CodeDTO(id="c4", name="club development", color=colors.code_green, count=4),
                CodeDTO(id="c5", name="facilities", color=colors.code_blue, count=1),
            ]
        ),
        CodeCategoryDTO(
            id="cat3",
            name="Motivation",
            codes=[
                CodeDTO(id="c6", name="cost concerns", color=colors.code_pink, count=2),
                CodeDTO(id="c7", name="learning enthusiasm", color=colors.code_cyan, count=6),
                CodeDTO(id="c8", name="time pressure", color=colors.code_orange, count=3),
            ]
        ),
    ]

    document = DocumentDTO(
        id="doc1",
        title="ID2.odt",
        badge="Case: ID2",
        content="""I have not studied much before. I know that I must get help as I have struggled understanding the lecture slides so far and searching the web did not help.

I really want someone to sit down with me and explain the course material. The tutors seem helpful but there are not enough of them to go around.

The course cost €200.00 and I do not want to waste my money. I have to make the most of this opportunity.

I really like learning new things. I think this course is good for me as I have wanted to learn about world history for a while. The structured content, lecture slides and web links have been really good. I guess some less computer-savvy people would have some trouble accessing the internet-based material, but its like a duck to water for me – no problem at all.

I get the feeling most students are having some problems with the coursework deadlines. There is much to learn and not many of us practice directed learning. We need more guidance on time management and prioritization.

Overall, I am satisfied with the club's facilities and the quality of instruction. The new training ground has made a big difference. I feel like I am improving week by week, which keeps me motivated to continue."""
    )

    document_stats = DocumentStatsDTO(
        overlapping_count=2,
        codes_applied=5,
        word_count=324,
    )

    selected_code = SelectedCodeDTO(
        id="c1",
        name="soccer playing",
        color=colors.code_yellow,
        memo="Code for references to playing soccer, including training, matches, and general participation in the sport.",
        example_text="I have not studied much before...",
    )

    overlapping_segments = [
        OverlappingSegmentDTO(segment_label="Segment 1", colors=[colors.code_green, colors.code_cyan]),
        OverlappingSegmentDTO(segment_label="Segment 2", colors=[colors.code_red, colors.code_orange]),
    ]

    file_memo = FileMemoDTO(
        memo="Participant ID2 interview transcript. Student is positive about the course but expresses concerns about workload and cost.",
        progress=65,
    )

    navigation = NavigationDTO(current=2, total=5)

    return TextCodingDataDTO(
        files=files,
        categories=categories,
        document=document,
        document_stats=document_stats,
        selected_code=selected_code,
        overlapping_segments=overlapping_segments,
        file_memo=file_memo,
        navigation=navigation,
        coders=["colin", "sarah", "james"],
        selected_coder="colin",
    )
