package com.identicum.config;

import com.fasterxml.jackson.core.JsonGenerator;
import com.fasterxml.jackson.databind.SerializerProvider;
import com.fasterxml.jackson.databind.ser.std.StdSerializer;
import com.identicum.models.Link;

import java.io.IOException;

public class LinkSimpleSerializer extends StdSerializer<Link> {

    public LinkSimpleSerializer() {
        this(null);
    }

    public LinkSimpleSerializer(Class<Link> t) {
        super(t);
    }

    @Override
    public void serialize(final Link link, JsonGenerator jsonGenerator, SerializerProvider serializerProvider) throws IOException {
        jsonGenerator.writeStartObject();
        jsonGenerator.writeStringField("display", link.getDisplay());
        jsonGenerator.writeStringField("color", link.getColor());
        jsonGenerator.writeStringField("icon", link.getIcon());
        jsonGenerator.writeStringField("target", link.getTarget());
        jsonGenerator.writeStringField("type", link.getType());
        jsonGenerator.writeEndObject();
    }
}
